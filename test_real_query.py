"""
تست با query واقعی
"""

import sys
import io
from crawler import MojavezCrawler
from datetime import datetime
from date_utils import format_date_for_api

# تنظیم encoding برای Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def test_real_query():
    """تست با query واقعی از curl"""
    print("="*60)
    print("تست با query واقعی")
    print("="*60)
    
    crawler = MojavezCrawler()
    
    # تاریخ‌ها: 1 بهمن 1404 تا 13 بهمن 1404
    # معادل میلادی: 21 ژانویه 2026 تا 2 فوریه 2026
    start_date = datetime(2026, 1, 21)
    end_date = datetime(2026, 2, 2)
    
    # تهران: province_id=33, township_id=3310
    province_id = 33
    township_id = 3310
    
    start_str = format_date_for_api(start_date)
    end_str = format_date_for_api(end_date)
    
    print(f"\nبازه زمانی: {start_str} تا {end_str}")
    print(f"استان ID: {province_id}, شهر ID: {township_id}")
    
    # تست 1: دریافت تعداد
    print("\n1. تست دریافت تعداد رکوردها...")
    count = crawler.get_records_count(start_str, end_str, province_id, township_id)
    print(f"   تعداد رکوردها: {count}")
    
    # تست 2: دریافت صفحه اول
    print("\n2. تست دریافت صفحه اول...")
    records = crawler.fetch_records(start_str, end_str, province_id, township_id, page=1)
    print(f"   تعداد رکوردهای دریافت شده: {len(records)}")
    if records:
        print(f"\n   نمونه رکورد اول:")
        import json
        print(json.dumps(records[0], indent=2, ensure_ascii=False)[:500])
    
    print("\n" + "="*60)
    print("تست تمام شد!")
    print("="*60)

if __name__ == "__main__":
    test_real_query()
