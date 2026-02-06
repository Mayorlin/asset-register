# Generated migration for Dashboard models

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('register', '0012_userprofile'),
    ]

    operations = [
        migrations.CreateModel(
            name='DashboardCache',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('cache_key', models.CharField(max_length=100, unique=True)),
                ('data', models.JSONField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Dashboard Cache',
                'verbose_name_plural': 'Dashboard Caches',
            },
        ),
        migrations.CreateModel(
            name='AssetMetrics',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField(unique=True)),
                ('total_assets', models.IntegerField(default=0)),
                ('active_assets', models.IntegerField(default=0)),
                ('in_use_assets', models.IntegerField(default=0)),
                ('spare_assets', models.IntegerField(default=0)),
                ('decommissioned_assets', models.IntegerField(default=0)),
                ('department_breakdown', models.JSONField(default=dict)),
                ('device_type_breakdown', models.JSONField(default=dict)),
                ('location_breakdown', models.JSONField(default=dict)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'Asset Metrics',
                'verbose_name_plural': 'Asset Metrics',
                'ordering': ['-date'],
            },
        ),
        migrations.CreateModel(
            name='ADUser',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('username', models.CharField(max_length=255, unique=True)),
                ('email', models.EmailField(blank=True, max_length=254, null=True)),
                ('first_name', models.CharField(blank=True, max_length=150)),
                ('last_name', models.CharField(blank=True, max_length=150)),
                ('display_name', models.CharField(blank=True, max_length=255)),
                ('employee_id', models.CharField(blank=True, max_length=50, null=True)),
                ('job_title', models.CharField(blank=True, max_length=150, null=True)),
                ('phone', models.CharField(blank=True, max_length=20, null=True)),
                ('is_active', models.BooleanField(default=True)),
                ('is_from_ad', models.BooleanField(default=False, help_text='Was this user imported from Active Directory?')),
                ('ad_guid', models.CharField(blank=True, help_text='Active Directory GUID', max_length=100, null=True, unique=True)),
                ('last_synced', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('department', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='ad_users',
                    to='register.department'
                )),
                ('office_location', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='ad_users',
                    to='register.location'
                )),
            ],
            options={
                'verbose_name': 'AD User',
                'verbose_name_plural': 'AD Users',
                'ordering': ['display_name', 'username'],
            },
        ),
    ]
