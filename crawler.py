"""
Crawler for qr.mojavez.ir
این کراولر با استفاده از GraphQL داده‌ها را از سایت مجوز.آی‌آر دریافت می‌کند
"""

import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import time
import logging
from date_utils import format_date_for_api

# تنظیمات لاگ
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('crawler.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class MojavezCrawler:
    """کراولر برای سایت qr.mojavez.ir"""
    
    # آدرس GraphQL endpoint (باید بررسی و اصلاح شود)
    GRAPHQL_ENDPOINT = "https://qr.mojavez.ir/graphql"
    
    # حداکثر تعداد رکورد در هر درخواست
    MAX_RECORDS_PER_REQUEST = 2100
    
    def __init__(self, endpoint: Optional[str] = None):
        """
        Initialize crawler
        
        Args:
            endpoint: آدرس GraphQL endpoint (اختیاری)
        """
        self.endpoint = endpoint or self.GRAPHQL_ENDPOINT
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
    def execute_query(self, query: str, variables: Optional[Dict] = None) -> Dict[str, Any]:
        """
        اجرای یک query در GraphQL
        
        Args:
            query: رشته GraphQL query
            variables: متغیرهای query
            
        Returns:
            پاسخ JSON از سرور
        """
        payload = {
            'query': query,
            'variables': variables or {}
        }
        
        max_retries = 10
        retry_delay = 2  # seconds
        
        for attempt in range(1, max_retries + 1):
            try:
                response = self.session.post(
                    self.endpoint,
                    json=payload,
                    timeout=180  # 3 minutes timeout for slow server
                )
                response.raise_for_status()
                return response.json()
            except requests.exceptions.Timeout as e:
                if attempt < max_retries:
                    logger.warning(f"⏱️ Query timeout (attempt {attempt}/{max_retries}): {e}. Retrying in {retry_delay}s...")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                    continue
                else:
                    logger.error(f"⏱️ Query timeout after {max_retries} attempts: {e}")
                    raise
            except requests.exceptions.RequestException as e:
                if attempt < max_retries:
                    logger.warning(f"❌ Query error (attempt {attempt}/{max_retries}): {e}. Retrying in {retry_delay}s...")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                    continue
                else:
                    logger.error(f"❌ Query error after {max_retries} attempts: {e}")
                    raise
    
    def get_records_count(
        self,
        start_date: str,
        end_date: str,
        province_id: Optional[int] = None,
        township_id: Optional[int] = None
    ) -> int:
        """
        دریافت تعداد رکوردها برای بازه زمانی مشخص
        
        Args:
            start_date: تاریخ شروع (فرمت: YYYY/M/D)
            end_date: تاریخ پایان (فرمت: YYYY/M/D)
            province_id: شناسه استان (اختیاری)
            township_id: شناسه شهر (اختیاری)
            
        Returns:
            تعداد رکوردها
        """
        # استفاده از countFilteredLicenses بر اساس schema واقعی
        count_query = """
        query CountFilteredLicenses($input: filterLicensesInput!) {
            countFilteredLicenses(input: $input) {
                total
            }
        }
        """
        
        # ساخت input object بر اساس ساختار واقعی
        input_obj = {
            "title": "",
            "name": "",
            "issue_start_date": "",
            "issue_end_date": "",
            "last_op_start_date": start_date,
            "last_op_end_date": end_date,
            "main_org_code": None,
            "sub_org_code": None
        }
        
        # اضافه کردن فیلترهای اختیاری
        if province_id:
            input_obj["province_id"] = province_id
        if township_id:
            input_obj["township_id"] = township_id
        
        variables = {
            'input': input_obj
        }
        
        try:
            result = self.execute_query(count_query, variables)
            
            # Check for errors
            if 'errors' in result:
                logger.error(f"❌ GraphQL errors: {result['errors']}")
                return 0
            
            # Response path: data.countFilteredLicenses.total
            count_result = result.get('data', {}).get('countFilteredLicenses', {})
            total = count_result.get('total', 0)
            logger.info(f"📊 Total records count: {total}")
            return total
        except Exception as e:
            logger.error(f"❌ Error getting records count: {e}")
            return 0
    
    def fetch_records(
        self,
        start_date: str,
        end_date: str,
        province_id: Optional[int] = None,
        township_id: Optional[int] = None,
        page: int = 1
    ) -> List[Dict[str, Any]]:
        """
        دریافت رکوردها از GraphQL
        
        Args:
            start_date: تاریخ شروع (فرمت: YYYY/M/D)
            end_date: تاریخ پایان (فرمت: YYYY/M/D)
            province_id: شناسه استان (اختیاری)
            township_id: شناسه شهر (اختیاری)
            page: شماره صفحه (شروع از 1) - باید به صورت String ارسال شود
            
        Returns:
            لیست رکوردها
        """
        # استفاده از filterLicenses بر اساس schema واقعی
        records_query = """
        query FilterLicenses($input: filterLicensesInput!) {
            filterLicenses(input: $input) {
                license {
                    request_number
                    applicant_name
                    user_image
                    license_title
                    organization_title
                    province_title
                    township_title
                    responded_at
                    status {
                        status_id
                        status_title
                        status_slug
                    }
                }
                pagination {
                    total
                    per_page
                    current_page
                }
            }
        }
        """
        
        # ساخت input object بر اساس ساختار واقعی
        input_obj = {
            "title": "",
            "name": "",
            "issue_start_date": "",
            "issue_end_date": "",
            "last_op_start_date": start_date,
            "last_op_end_date": end_date,
            "main_org_code": None,
            "sub_org_code": None,
            "page": str(page)  # page باید String باشد
            # Note: pageSize is not in the schema, API uses default page size
        }
        
        # اضافه کردن فیلترهای اختیاری
        if province_id:
            input_obj["province_id"] = province_id
        if township_id:
            input_obj["township_id"] = township_id
        
        variables = {
            'input': input_obj
        }
        
        try:
            result = self.execute_query(records_query, variables)
            
            # Check for errors
            if 'errors' in result:
                logger.error(f"❌ GraphQL errors: {result['errors']}")
                return []
            
            # مسیر پاسخ: data.filterLicenses.license
            filter_response = result.get('data', {}).get('filterLicenses', {})
            licenses = filter_response.get('license', [])
            
            # Debug: log full response structure
            logger.debug(f"🔍 Filter response keys: {filter_response.keys() if filter_response else 'None'}")
            
            # Log pagination info
            pagination = filter_response.get('pagination', {})
            pagination_info = {
                'total': 0,
                'per_page': 0,
                'current_page': 0,
                'total_pages': 0
            }
            
            if pagination:
                pagination_info['total'] = pagination.get('total') or 0
                pagination_info['per_page'] = pagination.get('per_page') or 0
                pagination_info['current_page'] = pagination.get('current_page') or 0
                if pagination_info['per_page'] and pagination_info['per_page'] > 0:
                    pagination_info['total_pages'] = (pagination_info['total'] + pagination_info['per_page'] - 1) // pagination_info['per_page']
                else:
                    pagination_info['total_pages'] = 0
                logger.info(f"📄 Page {pagination_info['current_page']}/{pagination_info['total_pages']} - Total: {pagination_info['total']}, Per page: {pagination_info['per_page']}")
            else:
                logger.warning(f"⚠️ No pagination info in response. Response structure: {list(filter_response.keys()) if filter_response else 'None'}")
            
            # Return records with pagination info
            return {
                'records': licenses,
                'pagination': pagination_info
            }
            
            return {
                'records': licenses,
                'pagination': pagination_info
            }
        except Exception as e:
            logger.error(f"❌ Error fetching records: {e}")
            return {'records': [], 'pagination': {'total': 0, 'per_page': 0, 'current_page': 0, 'total_pages': 0}}
    
    def get_provinces(self) -> List[Dict[str, Any]]:
        """
        دریافت لیست استان‌ها
        
        Returns:
            لیست استان‌ها با id و name
        """
        provinces_query = """
        query GetProvinces {
            provinceTownship {
                provinces {
                    id
                    name
                }
            }
        }
        """
        
        try:
            result = self.execute_query(provinces_query)
            province_township = result.get('data', {}).get('provinceTownship', {})
            provinces = province_township.get('provinces', [])
            return provinces
        except Exception as e:
            logger.error(f"❌ Error getting provinces list: {e}")
            return []
    
    def get_cities(self, province_id: int) -> List[Dict[str, Any]]:
        """
        دریافت لیست شهرهای یک استان
        
        Args:
            province_id: شناسه استان
            
        Returns:
            لیست شهرها با id و name
        """
        cities_query = """
        query GetTownships($provinceId: Int!) {
            provinceTownship {
                townships(provinceId: $provinceId) {
                    id
                    name
                }
            }
        }
        """
        
        try:
            result = self.execute_query(cities_query, {'provinceId': province_id})
            province_township = result.get('data', {}).get('provinceTownship', {})
            townships = province_township.get('townships', [])
            return townships
        except Exception as e:
            logger.error(f"❌ Error getting cities list: {e}")
            return []
    
    def split_date_range(self, start_date: datetime, end_date: datetime) -> List[tuple]:
        """
        تقسیم بازه زمانی به دو نیمه
        
        Args:
            start_date: تاریخ شروع
            end_date: تاریخ پایان
            
        Returns:
            لیست شامل دو tuple (start, end)
        """
        duration = end_date - start_date
        mid_date = start_date + duration / 2
        
        return [
            (start_date, mid_date),
            (mid_date + timedelta(days=1), end_date)
        ]
    
    def crawl_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        province_id: Optional[int] = None,
        township_id: Optional[int] = None,
        progress_callback: Optional[callable] = None,
        save_callback: Optional[callable] = None
    ) -> List[Dict[str, Any]]:
        """
        کراول کردن یک بازه زمانی با استراتژی تقسیم بازه
        
        Args:
            start_date: تاریخ شروع
            end_date: تاریخ پایان
            province_id: شناسه استان (اختیاری)
            township_id: شناسه شهر (اختیاری)
            
        Returns:
            لیست تمام رکوردها
        """
        start_str = format_date_for_api(start_date)
        end_str = format_date_for_api(end_date)
        
        logger.info(f"🔍 Checking range {start_str} to {end_str} - Province ID: {province_id or 'All'} - Township ID: {township_id or 'All'}")
        
        # Check records count
        count = self.get_records_count(start_str, end_str, province_id, township_id)
        logger.info(f"📊 Records count: {count}")
        
        # اگر تعداد کمتر از حد مجاز بود، مستقیماً دریافت می‌کنیم
        if count <= self.MAX_RECORDS_PER_REQUEST:
            logger.info(f"✅ Count ({count}) is within limit. Fetching all pages...")
            all_records = []
            page = 1
            max_pages = (count + 20) // 21 + 10  # Estimate max pages with buffer
            
            while page <= max_pages:
                result = self.fetch_records(
                    start_str, end_str, province_id, township_id,
                    page=page
                )
                
                # Handle new response structure
                if isinstance(result, dict):
                    records = result.get('records', [])
                    pagination = result.get('pagination', {})
                else:
                    records = result if result else []
                    pagination = {}
                
                if not records:
                    logger.info(f"ℹ️ No more records on page {page}")
                    break
                
                all_records.extend(records)
                logger.info(f"✅ Fetched {len(records)} records from page {page} (Total: {len(all_records)}/{count})")
                
                # Save records immediately via callback
                if save_callback:
                    saved = save_callback(records)
                    if saved > 0:
                        logger.info(f"💾 Saved {saved} records from page {page} to database")
                
                # Update progress via callback (after saving to ensure DB is updated)
                if progress_callback:
                    total_pages = pagination.get('total_pages', 0)
                    if total_pages == 0 and count > 0:
                        total_pages = (count + 20) // 21  # Estimate
                    # Progress callback will get actual count from database
                    progress_callback(len(all_records), page, total_pages)
                
                # Check if we've reached the last page
                total_pages = pagination.get('total_pages', 0)
                current_page = pagination.get('current_page', page)
                
                if total_pages > 0 and current_page >= total_pages:
                    logger.info(f"🏁 Reached last page according to pagination info: {current_page}/{total_pages}")
                    break
                
                # Check if we've fetched all expected records
                if len(all_records) >= count:
                    logger.info(f"✅ Fetched all expected records: {len(all_records)}/{count}")
                    break
                
                # Fallback: if records less than expected per page, might be last page
                # But only if we've fetched at least one full page
                if len(records) < 21 and page > 1:
                    logger.warning(f"⚠️ Got {len(records)} records (less than 21) on page {page}. Expected {count} total, got {len(all_records)}. Continuing...")
                    # Don't break, continue to make sure
                
                page += 1
                time.sleep(0.5)  # تاخیر کوتاه برای جلوگیری از rate limiting
            
            logger.info(f"📊 Finished fetching. Total: {len(all_records)}/{count} records")
            return all_records
        
        # اگر تعداد بیشتر از حد مجاز بود، بازه را تقسیم می‌کنیم
        duration = end_date - start_date
        
        # اگر بازه یک روزه است، بر اساس استان تقسیم می‌کنیم
        if duration.days == 0:
            if not province_id:
                # دریافت لیست استان‌ها و کراول کردن هر کدام
                provinces = self.get_provinces()
                all_records = []
                
                for prov in provinces:
                    prov_id = prov.get('id')
                    prov_name = prov.get('name', '')
                    logger.info(f"🌍 Crawling province: {prov_name} (ID: {prov_id})")
                    records = self.crawl_date_range(
                        start_date, end_date, province_id=prov_id,
                        progress_callback=progress_callback,
                        save_callback=save_callback
                    )
                    all_records.extend(records)
                    time.sleep(1)
                
                return all_records
            else:
                # اگر استان مشخص است، بر اساس شهر تقسیم می‌کنیم
                if not township_id:
                    cities = self.get_cities(province_id)
                    all_records = []
                    
                    for city_obj in cities:
                        city_id = city_obj.get('id')
                        city_name = city_obj.get('name', '')
                        logger.info(f"🏙️ Crawling city: {city_name} (ID: {city_id})")
                        records = self.crawl_date_range(
                            start_date, end_date, province_id=province_id, township_id=city_id,
                            progress_callback=progress_callback,
                            save_callback=save_callback
                        )
                        all_records.extend(records)
                        time.sleep(1)
                    
                    return all_records
                else:
                    # اگر شهر هم مشخص است و هنوز زیاد است، روز را به ساعت تقسیم می‌کنیم
                    logger.warning(f"⚠️ One-day range with specific city still too large ({count} records)! Splitting by hours...")
                    
                    # تقسیم روز به ساعت (هر 6 ساعت یک بازه)
                    all_records = []
                    current_time = start_date
                    hours_per_chunk = 6
                    
                    while current_time < end_date:
                        chunk_end = min(current_time + timedelta(hours=hours_per_chunk), end_date)
                        
                        chunk_start_str = format_date_for_api(current_time)
                        chunk_end_str = format_date_for_api(chunk_end)
                        
                        logger.info(f"⏰ Crawling hour range: {chunk_start_str} to {chunk_end_str}")
                        
                        # بررسی تعداد رکوردها در این بازه
                        chunk_count = self.get_records_count(chunk_start_str, chunk_end_str, province_id, township_id)
                        
                        if chunk_count <= self.MAX_RECORDS_PER_REQUEST:
                            # اگر کمتر از حد مجاز بود، مستقیماً دریافت می‌کنیم
                            chunk_records = self.fetch_records_with_pagination(
                                chunk_start_str, chunk_end_str, province_id, township_id
                            )
                            all_records.extend(chunk_records)
                            
                            # Save records immediately
                            if save_callback:
                                saved = save_callback(chunk_records)
                                if saved > 0:
                                    logger.info(f"💾 Saved {saved} records from hour chunk to database")
                            
                            # Update progress (after saving to ensure DB is updated)
                            if progress_callback:
                                progress_callback(len(all_records), 0, 0)
                        else:
                            # اگر هنوز زیاد بود، بازه را کوچکتر می‌کنیم (هر 1 ساعت)
                            logger.warning(f"⚠️ Hour range still too large ({chunk_count} records)! Splitting to 1-hour chunks...")
                            hour_start = current_time
                            
                            while hour_start < chunk_end:
                                hour_end = min(hour_start + timedelta(hours=1), chunk_end)
                                hour_start_str = format_date_for_api(hour_start)
                                hour_end_str = format_date_for_api(hour_end)
                                
                                logger.info(f"⏰ Crawling 1-hour range: {hour_start_str} to {hour_end_str}")
                                
                                hour_records = self.fetch_records_with_pagination(
                                    hour_start_str, hour_end_str, province_id, township_id
                                )
                                all_records.extend(hour_records)
                                
                                # Save records immediately
                                if save_callback:
                                    saved = save_callback(hour_records)
                                    if saved > 0:
                                        logger.info(f"💾 Saved {saved} records from 1-hour chunk to database")
                                
                                # Update progress
                                if progress_callback:
                                    progress_callback(len(all_records), 0, 0)
                                
                                hour_start = hour_end
                                time.sleep(0.5)
                        
                        current_time = chunk_end
                        time.sleep(0.5)
                    
                    return all_records
        
        # تقسیم بازه زمانی
        ranges = self.split_date_range(start_date, end_date)
        all_records = []
        
        for range_start, range_end in ranges:
            records = self.crawl_date_range(
                range_start, range_end, province_id, township_id,
                progress_callback=progress_callback,
                save_callback=save_callback
            )
            all_records.extend(records)
            time.sleep(1)
        
        return all_records
    
    
    def fetch_records_with_pagination(
        self,
        start_date: str,
        end_date: str,
        province_id: Optional[int] = None,
        township_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        دریافت رکوردها با pagination کامل
        
        Args:
            start_date: تاریخ شروع (فرمت: YYYY/M/D)
            end_date: تاریخ پایان (فرمت: YYYY/M/D)
            province_id: شناسه استان (اختیاری)
            township_id: شناسه شهر (اختیاری)
            
        Returns:
            لیست تمام رکوردها
        """
        all_records = []
        page = 1
        
        while True:
            result = self.fetch_records(
                start_date, end_date, province_id, township_id,
                page=page
            )
            
            # Handle new response structure
            if isinstance(result, dict):
                records = result.get('records', [])
                pagination = result.get('pagination', {})
            else:
                records = result if result else []
                pagination = {}
            
            if not records:
                break
            
            all_records.extend(records)
            logger.info(f"✅ Fetched {len(records)} records from page {page} (Total: {len(all_records)})")
            
            # Check if we've reached the last page
            total_pages = pagination.get('total_pages', 0)
            current_page = pagination.get('current_page', page)
            
            if total_pages > 0 and current_page >= total_pages:
                break
            
            # Fallback: if records less than 50, probably last page
            if len(records) < 50 and total_pages == 0:
                break
            
            page += 1
            time.sleep(0.5)
        
        return all_records
    
    def save_to_json(self, records: List[Dict], filename: str):
        """
        ذخیره رکوردها در فایل JSON
        
        Args:
            records: لیست رکوردها
            filename: نام فایل
        """
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(records, f, ensure_ascii=False, indent=2)
        logger.info(f"💾 Saved {len(records)} records to {filename}")


def main():
    """تابع اصلی برای اجرای کراولر"""
    crawler = MojavezCrawler()
    
    # مثال: کراول کردن یک بازه زمانی
    # تاریخ‌ها به میلادی (مثال: 1 بهمن 1404 = 21 ژانویه 2026)
    start_date = datetime(2026, 1, 21)
    end_date = datetime(2026, 2, 2)
    
    # تهران: province_id=33, township_id=3310
    province_id = 33
    township_id = 3310
    
    logger.info("🚀 Starting crawl...")
    records = crawler.crawl_date_range(start_date, end_date, province_id=province_id, township_id=township_id)
    
    logger.info(f"📊 Total records fetched: {len(records)}")
    
    # Save results
    output_file = f"records_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.json"
    crawler.save_to_json(records, output_file)
    
    logger.info("✅ Crawl completed successfully!")


if __name__ == "__main__":
    main()
