# راه‌اندازی نهایی

## ✅ مراحل انجام شده

1. ✅ پروژه Django ایجاد شد
2. ✅ Models ایجاد شدند
3. ✅ Migrations انجام شد
4. ✅ SQLite به عنوان دیتابیس پیش‌فرض تنظیم شد

## 🚀 مراحل بعدی

### 1. ایجاد Superuser (اگر انجام نشده)

```powershell
python create_superuser.py
```

یا دستی:
```powershell
python manage.py createsuperuser
```

### 2. راه‌اندازی Celery Worker

در یک terminal جدید:
```powershell
celery -A crawler_panel worker --loglevel=info --pool=threads --concurrency=4
```

یا:
```powershell
.\manage_celery.bat
```

### 3. راه‌اندازی Django Server

```powershell
python manage.py runserver
```

یا:
```powershell
.\run_server.bat
```

### 4. دسترسی

- **پنل اصلی**: http://localhost:8000
- **Django Admin**: http://localhost:8000/admin
  - Username: `admin`
  - Password: `admin123` (یا آنچه در create_superuser.py تنظیم کردید)

## 📝 نکات مهم

1. **Celery Worker باید همیشه در حال اجرا باشد** - بدون آن کراول‌ها اجرا نمی‌شوند
2. **SQLite برای development** - برای production از PostgreSQL استفاده کنید
3. **Redis باید در دسترس باشد** - برای Celery

## 🔄 تغییر به PostgreSQL

برای استفاده از PostgreSQL در production:

1. فایل `.env` را ایجاد کنید:
```env
USE_SQLITE=False
DATABASE_URL=postgres://postgres:04cTAnvcHRbwr0T9cXXB@666dc316-12f4-49f3-987f-ca1a0781a9fa.hadb.ir:26641/postgres
```

2. Migrations را دوباره اجرا کنید:
```powershell
python manage.py migrate
```

## ✅ همه چیز آماده است!
