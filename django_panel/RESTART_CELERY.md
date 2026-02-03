# 🔄 Restart Celery Worker

## مشکل
اگر هنوز خطای `is_aborted` را می‌بینید، Celery worker باید restart شود.

## راه حل

### 1. متوقف کردن Celery Worker فعلی
در terminal که Celery worker در حال اجرا است:
- `Ctrl + C` را بزنید

### 2. پاک کردن Cache (اختیاری)
```powershell
cd D:\Git\Mojavez\django_panel
Remove-Item -Recurse -Force jobs\__pycache__
Remove-Item -Recurse -Force crawler_panel\__pycache__
```

### 3. راه‌اندازی مجدد Celery Worker
```powershell
celery -A crawler_panel worker --loglevel=info --pool=threads --concurrency=4
```

یا:
```powershell
.\manage_celery.bat
```

## ✅ بعد از restart
- خطای `is_aborted` دیگر نباید ظاهر شود
- لاگ‌های جدید با emoji نمایش داده می‌شوند
