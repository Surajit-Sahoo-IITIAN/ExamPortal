"""
Automatic Database Seeder for Production Deployments
Ensures Superuser (SurajitSahoo) and all 100 Student Accounts exist with passwords from students_credentials.csv
"""

import os
import csv
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'examportal.settings')
django.setup()

from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password

def init_db():
    print("=" * 60)
    print("  SEEDING PRODUCTION DATABASE")
    print("=" * 60)

    # 1. Ensure Superuser exists
    admin_user, created = User.objects.get_or_create(
        username='SurajitSahoo',
        defaults={'is_staff': True, 'is_superuser': True}
    )
    admin_user.set_password('admin123')
    admin_user.is_staff = True
    admin_user.is_superuser = True
    admin_user.save()
    print(f"  • Instructor/Admin: SurajitSahoo (Password: admin123) - {'Created' if created else 'Verified'}")

    # 2. Seed 100 Students from students_credentials.csv
    csv_path = 'students_credentials.csv'
    if not os.path.exists(csv_path):
        print(f"  ❌ Error: {csv_path} not found!")
        return

    users_to_update = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            username = row.get('Roll Number / Username', '').strip()
            password = row.get('Password', '').strip()

            if not username or not password:
                continue

            user, _ = User.objects.get_or_create(
                username=username,
                defaults={'is_staff': False, 'is_superuser': False}
            )
            user.password = make_password(password)
            user.is_staff = False
            user.is_superuser = False
            users_to_update.append(user)

    User.objects.bulk_update(users_to_update, ['password', 'is_staff', 'is_superuser'])
    print(f"  • Students Seeded: {len(users_to_update)} accounts verified from {csv_path}")
    print("=" * 60)
    print("  PRODUCTION DATABASE READY!")
    print("=" * 60)

if __name__ == '__main__':
    init_db()
