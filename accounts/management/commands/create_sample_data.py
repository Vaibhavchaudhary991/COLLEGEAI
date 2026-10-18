"""
Management command: create_sample_data
Creates a demo admin user, demo student user, and sample documents.

Usage: python manage.py create_sample_data
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = 'Create sample admin and student users for development/testing'

    def handle(self, *args, **options):
        self._create_admin()
        self._create_student()
        self.stdout.write(self.style.SUCCESS('\nSample data created successfully!\n'))
        self.stdout.write('-' * 40)
        self.stdout.write('Admin   -> username: admin       password: admin123')
        self.stdout.write('Student -> username: student     password: student123')
        self.stdout.write('-' * 40)

    def _create_admin(self):
        if User.objects.filter(username='admin').exists():
            self.stdout.write(self.style.WARNING('Admin user already exists, skipping.'))
            return
        User.objects.create_superuser(
            username='admin',
            email='admin@collegeai.dev',
            password='admin123',
            first_name='Admin',
            last_name='User',
            role=User.ROLE_ADMIN,
        )
        self.stdout.write(self.style.SUCCESS('[OK] Admin user created (username: admin, password: admin123)'))

    def _create_student(self):
        if User.objects.filter(username='student').exists():
            self.stdout.write(self.style.WARNING('Student user already exists, skipping.'))
            return
        User.objects.create_user(
            username='student',
            email='student@collegeai.dev',
            password='student123',
            first_name='Jane',
            last_name='Student',
            role=User.ROLE_STUDENT,
        )
        self.stdout.write(self.style.SUCCESS('[OK] Student user created (username: student, password: student123)'))
