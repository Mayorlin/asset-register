#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate

# Create superuser with admin role if it doesn't exist
if [ "$CREATE_SUPERUSER" ]; then
  python manage.py shell << END
from django.contrib.auth import get_user_model
import os

User = get_user_model()
username = os.environ.get('DJANGO_SUPERUSER_USERNAME')
email = os.environ.get('DJANGO_SUPERUSER_EMAIL')
password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')

if username and email and password:
    if not User.objects.filter(username=username).exists():
        user = User.objects.create_superuser(username, email, password)
        # Set the profile role to admin
        user.profile.role = 'admin'
        user.profile.save()
        print(f'Superuser {username} created successfully with admin role')
    else:
        # If user exists but has wrong role, update it
        user = User.objects.get(username=username)
        user.profile.role = 'admin'
        user.profile.save()
        print(f'Updated {username} to admin role')
else:
    print('Superuser credentials not provided')
END
fi