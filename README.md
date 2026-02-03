# Crawler for qr.mojavez.ir

این پروژه یک کراولر برای دریافت داده‌ها از سایت `qr.mojavez.ir` با استفاده از GraphQL است.

## ویژگی‌ها

- استفاده از GraphQL برای دریافت داده‌ها
- استراتژی تقسیم بازه زمانی برای مقابله با محدودیت 2100 رکورد
- تقسیم بر اساس استان، شهر و ساعت در صورت نیاز
- ذخیره نتایج در فایل JSON
- لاگ کردن تمام عملیات

## نصب

```bash
pip install -r requirements.txt
```

## استفاده

### استفاده پایه

```python
from crawler import MojavezCrawler
from datetime import datetime

crawler = MojavezCrawler()

# کراول کردن یک بازه زمانی
start_date = datetime(2024, 1, 1)
end_date = datetime(2024, 1, 31)

records = crawler.crawl_date_range(start_date, end_date)

# ذخیره نتایج
crawler.save_to_json(records, "output.json")
```

### مثال‌های بیشتر

فایل `example_usage.py` شامل مثال‌های مختلف استفاده است:

```bash
python example_usage.py
```

### اجرای مستقیم

```bash
python crawler.py
```

## استراتژی کراول

کراولر به صورت خودکار بازه‌های زمانی را تقسیم می‌کند:

1. **بازه زمانی**: اگر تعداد رکوردها بیشتر از 2100 باشد، بازه به دو نیمه تقسیم می‌شود
2. **استان**: اگر بازه یک روزه باشد و تعداد زیاد باشد، بر اساس استان تقسیم می‌شود
3. **شهر**: اگر استان مشخص باشد و تعداد زیاد باشد، بر اساس شهر تقسیم می‌شود
4. **ساعت**: اگر شهر هم مشخص باشد و تعداد زیاد باشد، بر اساس ساعت تقسیم می‌شود

## تنظیمات

قبل از استفاده، باید GraphQL queries را بر اساس schema واقعی سایت تنظیم کنید:

### مرحله 1: شناسایی GraphQL Endpoint

از اسکریپت `inspect_api.py` برای پیدا کردن endpoint استفاده کنید:

```bash
python inspect_api.py
```

این اسکریپت endpointهای احتمالی را تست می‌کند و schema را دریافت می‌کند.

### مرحله 2: بررسی Queries واقعی

1. سایت را در مرورگر باز کنید (https://qr.mojavez.ir/)
2. Developer Tools (F12) را باز کنید
3. به Network tab بروید
4. یک جستجو انجام دهید
5. GraphQL request را پیدا کنید و query را کپی کنید

### مرحله 3: به‌روزرسانی Crawler

Queries واقعی را در متدهای زیر در `crawler.py` قرار دهید:
- `get_records_count()` - برای دریافت تعداد رکوردها
- `fetch_records()` - برای دریافت رکوردها
- `get_provinces()` - برای دریافت لیست استان‌ها
- `get_cities()` - برای دریافت لیست شهرها

## لاگ

تمام عملیات در فایل `crawler.log` ذخیره می‌شوند.

## فایل‌های پروژه

- `crawler.py` - کراولر اصلی
- `inspect_api.py` - شناسایی GraphQL endpoint و schema
- `discover_schema.py` - شناسایی schema با Selenium (اختیاری)
- `example_usage.py` - مثال‌های استفاده
- `requirements.txt` - وابستگی‌های پروژه

## نکات مهم

- رعایت `robots.txt` و شرایط استفاده سایت
- استفاده از تاخیر مناسب بین درخواست‌ها برای جلوگیری از rate limiting
- بررسی و اصلاح GraphQL queries بر اساس schema واقعی
- قبل از اجرای کراولر، حتماً endpoint و queries را تنظیم کنید
