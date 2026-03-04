"""Utility to print Django user list from current project."""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecosite.settings')
django.setup()

from django.contrib.auth import get_user_model

users = get_user_model().objects.all()
print(list(users.values_list('id', 'username')))
