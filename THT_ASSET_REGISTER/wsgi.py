"""
WSGI config for THT_ASSET_REGISTER project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "THT_ASSET_REGISTER.settings")

application = get_wsgi_application()


#SuperUser Creation (One-Time Use)
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'gabriel.oyemomi', 'Oluwamayowagabriel@2002')