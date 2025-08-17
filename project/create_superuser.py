#!/usr/bin/env python
"""
Script to create a superuser for the Django application
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'stock_management.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

def create_superuser():
    if not User.objects.filter(username='admin').exists():
        User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='admin123',
            role='admin'
        )
        print("Superuser 'admin' created successfully!")
        print("Username: admin")
        print("Password: admin123")
    else:
        print("Superuser 'admin' already exists.")

if __name__ == '__main__':
    create_superuser()