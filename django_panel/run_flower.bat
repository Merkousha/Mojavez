@echo off
REM Flower uses the same Redis as in settings (REDIS_HOST, REDIS_PORT, REDIS_PASSWORD from env or .env)
echo Starting Flower at http://localhost:5555 ...
celery -A crawler_panel flower --port=5555
