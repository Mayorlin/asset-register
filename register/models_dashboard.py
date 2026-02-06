from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta


class DashboardCache(models.Model):
    """
    Cache for dashboard statistics to improve performance
    """
    cache_key = models.CharField(max_length=100, unique=True)
    data = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Dashboard Cache"
        verbose_name_plural = "Dashboard Caches"
    
    def __str__(self):
        return f"{self.cache_key} - {self.updated_at}"
    
    @classmethod
    def get_or_compute(cls, key, compute_function, ttl_minutes=30):
        """
        Get cached data or compute if expired
        """
        try:
            cache_obj = cls.objects.get(cache_key=key)
            # Check if cache is still valid
            if timezone.now() - cache_obj.updated_at < timedelta(minutes=ttl_minutes):
                return cache_obj.data
        except cls.DoesNotExist:
            pass
        
        # Compute new data
        data = compute_function()
        
        # Update or create cache
        cls.objects.update_or_create(
            cache_key=key,
            defaults={'data': data}
        )
        
        return data


class ADUser(models.Model):
    """
    Model to store Active Directory users for asset assignment
    Can be synced from AD or manually added
    """
    username = models.CharField(max_length=255, unique=True)
    email = models.EmailField(blank=True, null=True)
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    display_name = models.CharField(max_length=255, blank=True)
    department = models.ForeignKey(
        'Department',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ad_users'
    )
    employee_id = models.CharField(max_length=50, blank=True, null=True)
    job_title = models.CharField(max_length=150, blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    office_location = models.ForeignKey(
        'Location',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ad_users'
    )
    
    # AD sync fields
    is_active = models.BooleanField(default=True)
    is_from_ad = models.BooleanField(
        default=False,
        help_text="Was this user imported from Active Directory?"
    )
    ad_guid = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        unique=True,
        help_text="Active Directory GUID"
    )
    last_synced = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "AD User"
        verbose_name_plural = "AD Users"
        ordering = ['display_name', 'username']
    
    def __str__(self):
        if self.display_name:
            return f"{self.display_name} ({self.username})"
        return self.username
    
    @property
    def full_name(self):
        if self.first_name or self.last_name:
            return f"{self.first_name} {self.last_name}".strip()
        return self.display_name or self.username
    
    def get_assigned_assets_count(self):
        """Get number of assets assigned to this user"""
        from .models import Asset
        return Asset.objects.filter(
            staff_name__icontains=self.username
        ).exclude(
            status__name__iexact='decommissioned'
        ).count()


class AssetMetrics(models.Model):
    """
    Store daily/weekly/monthly asset metrics for trending
    """
    date = models.DateField(unique=True)
    total_assets = models.IntegerField(default=0)
    active_assets = models.IntegerField(default=0)
    in_use_assets = models.IntegerField(default=0)
    spare_assets = models.IntegerField(default=0)
    decommissioned_assets = models.IntegerField(default=0)
    
    # By department (JSON for flexibility)
    department_breakdown = models.JSONField(default=dict)
    device_type_breakdown = models.JSONField(default=dict)
    location_breakdown = models.JSONField(default=dict)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Asset Metrics"
        verbose_name_plural = "Asset Metrics"
        ordering = ['-date']
    
    def __str__(self):
        return f"Metrics for {self.date}"
    
    @classmethod
    def generate_for_date(cls, date):
        """
        Generate metrics snapshot for a specific date
        """
        from .models import Asset, DeviceStatus
        from collections import Counter
        
        # Get all assets (excluding decommissioned for most counts)
        all_assets = Asset.objects.select_related(
            'status', 'device_type', 'department', 'location'
        ).all()
        
        active_assets = all_assets.exclude(status__name__iexact='decommissioned')
        
        # Count by status
        try:
            decommissioned_status = DeviceStatus.objects.get(name__iexact='decommissioned')
            decommissioned_count = all_assets.filter(status=decommissioned_status).count()
        except DeviceStatus.DoesNotExist:
            decommissioned_count = 0
        
        # Department breakdown
        dept_counter = Counter(
            asset.department.name if asset.department else 'Unassigned'
            for asset in active_assets
        )
        
        # Device type breakdown
        device_counter = Counter(
            asset.device_type.name if asset.device_type else 'Unknown'
            for asset in active_assets
        )
        
        # Location breakdown
        location_counter = Counter(
            asset.location.name if asset.location else 'Unknown'
            for asset in active_assets
        )
        
        # Status counts
        status_counts = Counter(asset.status.name for asset in active_assets)
        
        metrics, created = cls.objects.update_or_create(
            date=date,
            defaults={
                'total_assets': all_assets.count(),
                'active_assets': active_assets.count(),
                'in_use_assets': status_counts.get('in_use', 0),
                'spare_assets': status_counts.get('spare', 0),
                'decommissioned_assets': decommissioned_count,
                'department_breakdown': dict(dept_counter),
                'device_type_breakdown': dict(device_counter),
                'location_breakdown': dict(location_counter),
            }
        )
        
        return metrics
