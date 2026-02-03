"""
مثال استفاده از کراولر
"""

from crawler import MojavezCrawler
from datetime import datetime, timedelta
import json


def example_basic_crawl():
    """مثال ساده: کراول کردن یک بازه زمانی"""
    print("مثال 1: کراول ساده")
    print("-" * 50)
    
    crawler = MojavezCrawler()
    
    # کراول کردن یک ماه
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2024, 1, 31)
    
    records = crawler.crawl_date_range(start_date, end_date)
    
    print(f"تعداد رکوردهای دریافت شده: {len(records)}")
    crawler.save_to_json(records, "example_output.json")


def example_province_crawl():
    """مثال: کراول کردن یک استان خاص"""
    print("\nمثال 2: کراول یک استان")
    print("-" * 50)
    
    crawler = MojavezCrawler()
    
    # کراول کردن تهران در یک بازه زمانی
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2024, 1, 7)
    
    records = crawler.crawl_date_range(
        start_date, 
        end_date, 
        province="تهران"
    )
    
    print(f"تعداد رکوردهای تهران: {len(records)}")
    crawler.save_to_json(records, "tehran_records.json")


def example_custom_endpoint():
    """مثال: استفاده از endpoint سفارشی"""
    print("\nمثال 3: استفاده از endpoint سفارشی")
    print("-" * 50)
    
    # اگر endpoint متفاوتی دارید
    custom_endpoint = "https://qr.mojavez.ir/graphql"
    crawler = MojavezCrawler(endpoint=custom_endpoint)
    
    # تست یک query ساده
    test_query = """
    query {
        __typename
    }
    """
    
    result = crawler.execute_query(test_query)
    print(f"نتیجه تست: {json.dumps(result, indent=2, ensure_ascii=False)}")


def example_step_by_step():
    """مثال: کراول مرحله به مرحله"""
    print("\nمثال 4: کراول مرحله به مرحله")
    print("-" * 50)
    
    crawler = MojavezCrawler()
    
    # 1. دریافت لیست استان‌ها
    print("1. دریافت لیست استان‌ها...")
    provinces = crawler.get_provinces()
    print(f"تعداد استان‌ها: {len(provinces)}")
    print(f"نمونه: {provinces[:5]}")
    
    # 2. دریافت لیست شهرهای یک استان
    if provinces:
        print(f"\n2. دریافت شهرهای استان {provinces[0]}...")
        cities = crawler.get_cities(provinces[0])
        print(f"تعداد شهرها: {len(cities)}")
        print(f"نمونه: {cities[:5]}")
    
    # 3. بررسی تعداد رکوردها
    print("\n3. بررسی تعداد رکوردها...")
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2024, 1, 31)
    
    count = crawler.get_records_count(
        start_date.strftime('%Y-%m-%d'),
        end_date.strftime('%Y-%m-%d')
    )
    print(f"تعداد رکوردها در بازه {start_date.date()} تا {end_date.date()}: {count}")


if __name__ == "__main__":
    print("=" * 60)
    print("مثال‌های استفاده از کراولر")
    print("=" * 60)
    
    # قبل از اجرا، باید GraphQL queries را تنظیم کنید
    print("\n⚠️ توجه: قبل از اجرا، GraphQL queries را در crawler.py تنظیم کنید!")
    print("از discover_schema.py برای پیدا کردن schema استفاده کنید.\n")
    
    # مثال‌ها (comment کنید تا اجرا نشوند)
    # example_basic_crawl()
    # example_province_crawl()
    # example_custom_endpoint()
    # example_step_by_step()
    
    print("\nبرای اجرای مثال‌ها، comment را از خطوط بالا بردارید.")
