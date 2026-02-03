# تنظیمات دیتابیس

## استفاده از SQLite (Development - پیش‌فرض)

پروژه به صورت پیش‌فرض از SQLite استفاده می‌کند. نیازی به تنظیمات اضافی نیست.

## استفاده از PostgreSQL (Production)

برای استفاده از PostgreSQL:

### 1. ایجاد فایل .env

```env
USE_SQLITE=False
DATABASE_URL=postgres://postgres:04cTAnvcHRbwr0T9cXXB@666dc316-12f4-49f3-987f-ca1a0781a9fa.hadb.ir:26641/postgres
```

### 2. بررسی اتصال

```bash
python test_db_connection.py
```

### 3. اجرای migrations

```bash
python manage.py migrate
```

## نکات مهم

- در development از SQLite استفاده کنید (سریع‌تر و ساده‌تر)
- در production از PostgreSQL استفاده کنید
- اگر PostgreSQL در دسترس نباشد، به صورت خودکار به SQLite fallback می‌کند
