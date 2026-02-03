# پنل مدیریت کراولر - Django + Celery

پنل وب کامل برای مدیریت کراول‌های qr.mojavez.ir با Django و Celery

## ویژگی‌ها

- ✅ Django + PostgreSQL برای دیتابیس
- ✅ Celery + Redis برای background tasks
- ✅ Django REST Framework برای API
- ✅ Django Admin برای مدیریت
- ✅ Frontend زیبا و responsive
- ✅ نظارت بر پیشرفت در زمان واقعی

## نصب و راه‌اندازی

### 1. نصب وابستگی‌ها

```bash
cd django_panel
python -m pip install -r requirements.txt
```

### 2. تنظیم دیتابیس

```bash
python manage.py migrate
```

### 3. ایجاد superuser (برای Django Admin)

```bash
python manage.py createsuperuser
```

### 4. راه‌اندازی Redis

Redis باید در حال اجرا باشد. connection string در settings.py تنظیم شده است.

### 5. راه‌اندازی Celery Worker

در یک terminal جداگانه:

```bash
cd django_panel
celery -A crawler_panel worker --loglevel=info
```

### 6. راه‌اندازی Django Server

```bash
python manage.py runserver
```

### 7. (اختیاری) راه‌اندازی Flower (Monitoring)

```bash
celery -A crawler_panel flower
```

سپس باز کنید: http://localhost:5555

## دسترسی

- **پنل اصلی**: http://localhost:8000
- **Django Admin**: http://localhost:8000/admin
- **API**: http://localhost:8000/api/
- **Flower**: http://localhost:5555 (اگر اجرا شده باشد)

## ساختار پروژه

```
django_panel/
├── manage.py
├── requirements.txt
├── crawler_panel/
│   ├── settings.py      # تنظیمات Django + Celery
│   ├── urls.py
│   ├── celery.py        # تنظیمات Celery
│   └── __init__.py
├── jobs/
│   ├── models.py        # CrawlJob, CrawlRecord
│   ├── admin.py         # Django Admin
│   ├── views.py         # API Views
│   ├── serializers.py   # DRF Serializers
│   ├── tasks.py         # Celery Tasks
│   ├── urls.py
│   └── templates/jobs/
│       └── index.html
└── static/
    ├── style.css
    └── script.js
```

## API Endpoints

- `GET /api/jobs/` - لیست کراول‌ها
- `POST /api/jobs/` - ایجاد کراول جدید
- `GET /api/jobs/{id}/` - اطلاعات یک کراول
- `POST /api/jobs/{id}/start/` - شروع کراول
- `POST /api/jobs/{id}/cancel/` - لغو کراول
- `DELETE /api/jobs/{id}/` - حذف کراول
- `GET /api/jobs/{id}/records/` - رکوردهای یک کراول
- `GET /api/stats/` - آمار کلی

## استفاده

1. باز کردن پنل در مرورگر
2. پر کردن فرم ایجاد کراول
3. کراول به صورت خودکار در Celery worker اجرا می‌شود
4. مشاهده پیشرفت در پنل
5. مشاهده رکوردها

## نکات مهم

- Celery worker باید همیشه در حال اجرا باشد
- Redis باید در دسترس باشد
- PostgreSQL connection string در settings.py تنظیم شده است
- برای production، DEBUG را False کنید
