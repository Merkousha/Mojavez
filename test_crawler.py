"""
تست کراولر با queryهای واقعی
"""

import sys
import io
from crawler import MojavezCrawler
from datetime import datetime

# تنظیم encoding برای Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def test_basic():
    """تست پایه کراولر"""
    print("="*60)
    print("تست کراولر")
    print("="*60)
    
    crawler = MojavezCrawler()
    
    # تست 1: دریافت لیست استان‌ها
    print("\n1. تست دریافت لیست استان‌ها...")
    provinces = crawler.get_provinces()
    print(f"   تعداد استان‌ها: {len(provinces)}")
    if provinces:
        print(f"   نمونه: {provinces[0]}")
    
    # تست 2: دریافت تعداد رکوردها
    print("\n2. تست دریافت تعداد رکوردها...")
    start_date = "2024-01-01"
    end_date = "2024-01-31"
    count = crawler.get_records_count(start_date, end_date)
    print(f"   تعداد رکوردها در بازه {start_date} تا {end_date}: {count}")
    
    # تست 3: دریافت رکوردها (صفحه اول)
    print("\n3. تست دریافت رکوردها (صفحه اول)...")
    records = crawler.fetch_records(start_date, end_date, page=1, page_size=10)
    print(f"   تعداد رکوردهای دریافت شده: {len(records)}")
    if records:
        print(f"   نمونه رکورد:")
        print(f"   {records[0]}")
    
    print("\n" + "="*60)
    print("تست‌ها تمام شد!")
    print("="*60)

if __name__ == "__main__":
    test_basic()
