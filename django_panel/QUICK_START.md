# راه‌اندازی سریع

## در PowerShell:

### 1. نصب وابستگی‌ها
```powershell
python -m pip install -r requirements.txt
```

### 2. ایجاد دیتابیس
```powershell
python manage.py migrate
```

### 3. ایجاد superuser (برای Admin)
```powershell
python manage.py createsuperuser
```

### 4. راه‌اندازی Celery Worker
در یک terminal جدید:
```powershell
celery -A crawler_panel worker --loglevel=info --pool=threads --concurrency=4
```

یا از فایل bat:
```powershell
.\manage_celery.bat
```

### 5. راه‌اندازی Django Server
در terminal اصلی:
```powershell
python manage.py runserver
```

یا از فایل bat:
```powershell
.\run_server.bat
```

### 6. دسترسی
- پنل: http://localhost:8000
- Admin: http://localhost:8000/admin

## نکته مهم

**باید دو terminal باز کنید:**
1. یکی برای Celery Worker
2. یکی برای Django Server

بدون Celery Worker، کراول‌ها اجرا نمی‌شوند!
