"""
اسکریپت ایجاد superuser
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crawler_panel.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

username = 'admin'
email = 'admin@example.com'
password = 'admin123'  # در production تغییر دهید!

if User.objects.filter(username=username).exists():
    print(f"User '{username}' already exists!")
else:
    User.objects.create_superuser(username=username, email=email, password=password)
    print(f"Superuser '{username}' created successfully!")
    print(f"Username: {username}")
    print(f"Password: {password}")
