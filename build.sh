#!/usr/bin/env bash
# exit on error
set -o errexit

pip install -r requirements.txt

python manage.py collectstatic --no-input
python manage.py migrate

# Create superuser if it doesn't exist
# The '|| true' ensures the build doesn't fail if the user already exists
if [ "$CREATE_SUPERUSER" ]; then
  python manage.py createsuperuser --noinput || true
fi