from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta, date
from collections import Counter
import json


def get_dashboard_stats():
    """
    Get comprehensive dashboard statistics
    """
    from .models import Asset, DeviceStatus, DeviceType, Department, AuditLog
    
    # Get decommissioned status
    try:
        decommissioned_status = DeviceStatus.objects.get(name__iexact='decommissioned')
    except DeviceStatus.DoesNotExist:
        decommissioned_status = None
    
    # Active assets (excluding decommissioned)
    active_assets = Asset.objects.all()
    if decommissioned_status:
        active_assets = active_assets.exclude(status=decommissioned_status)
    
    # Total counts
    total_assets = Asset.objects.count()
    active_count = active_assets.count()
    decommissioned_count = total_assets - active_count
    
    # Status breakdown
    status_breakdown = list(
        active_assets.values('status__name')
        .annotate(count=Count('id'))
        .order_by('-count')
    )
    
    # Device type breakdown
    device_type_breakdown = list(
        active_assets.values('device_type__name')
        .annotate(count=Count('id'))
        .order_by('-count')
    )
    
    # Department breakdown
    department_breakdown = list(
        active_assets.values('department__name')
        .annotate(count=Count('id'))
        .order_by('-count')
    )
    
    # Location breakdown
    location_breakdown = list(
        active_assets.values('location__name')
        .annotate(count=Count('id'))
        .order_by('-count')
    )
    
    # Recent activity (last 10 audit logs)
    recent_activity = list(
        AuditLog.objects.select_related('asset', 'user')
        .order_by('-timestamp')[:10]
        .values(
            'action',
            'asset__device_name',
            'asset__serial_number',
            'user__username',
            'timestamp',
            'field_name',
            'old_value',
            'new_value'
        )
    )
    
    # Assets created this month
    first_day_of_month = date.today().replace(day=1)
    assets_this_month = active_assets.filter(
        created_at__gte=first_day_of_month
    ).count()
    
    # Assets updated this week
    week_ago = timezone.now() - timedelta(days=7)
    assets_updated_this_week = active_assets.filter(
        updated_at__gte=week_ago
    ).count()
    
    return {
        'total_assets': total_assets,
        'active_assets': active_count,
        'decommissioned_assets': decommissioned_count,
        'assets_this_month': assets_this_month,
        'assets_updated_this_week': assets_updated_this_week,
        'status_breakdown': status_breakdown,
        'device_type_breakdown': device_type_breakdown,
        'department_breakdown': department_breakdown,
        'location_breakdown': location_breakdown,
        'recent_activity': recent_activity,
    }


def get_trend_data(days=30):
    """
    Get asset trend data for the last N days
    """
    from .models import Asset
    from django.db.models.functions import TruncDate
    
    start_date = timezone.now() - timedelta(days=days)
    
    # Assets created per day
    created_trend = list(
        Asset.objects.filter(created_at__gte=start_date)
        .annotate(date=TruncDate('created_at'))
        .values('date')
        .annotate(count=Count('id'))
        .order_by('date')
    )
    
    # Assets updated per day
    updated_trend = list(
        Asset.objects.filter(updated_at__gte=start_date)
        .annotate(date=TruncDate('updated_at'))
        .values('date')
        .annotate(count=Count('id'))
        .order_by('date')
    )
    
    return {
        'created_trend': created_trend,
        'updated_trend': updated_trend,
    }


def get_department_analytics():
    """
    Get detailed analytics per department
    """
    from .models import Asset, Department, DeviceStatus
    
    try:
        decommissioned_status = DeviceStatus.objects.get(name__iexact='decommissioned')
    except DeviceStatus.DoesNotExist:
        decommissioned_status = None
    
    departments = Department.objects.all()
    analytics = []
    
    for dept in departments:
        assets = Asset.objects.filter(department=dept)
        if decommissioned_status:
            active_assets = assets.exclude(status=decommissioned_status)
        else:
            active_assets = assets
        
        # Device types in this department
        device_types = list(
            active_assets.values('device_type__name')
            .annotate(count=Count('id'))
        )
        
        analytics.append({
            'department': dept.name,
            'total_assets': active_assets.count(),
            'device_types': device_types,
        })
    
    return analytics


def search_ad_users(query):
    """
    Search for AD users (will be enhanced when AD integration is active)
    For now, searches the ADUser model
    """
    from .models_dashboard import ADUser
    
    if not query or len(query) < 2:
        return []
    
    users = ADUser.objects.filter(
        Q(username__icontains=query) |
        Q(email__icontains=query) |
        Q(first_name__icontains=query) |
        Q(last_name__icontains=query) |
        Q(display_name__icontains=query)
    ).filter(is_active=True)[:20]
    
    return [
        {
            'id': user.id,
            'username': user.username,
            'display_name': user.full_name,
            'email': user.email,
            'department': user.department.name if user.department else '',
            'job_title': user.job_title or '',
        }
        for user in users
    ]


def sync_ad_users_stub():
    """
    Placeholder for Active Directory sync
    This will be implemented when AD integration is configured
    """
    # TODO: Implement LDAP connection and sync
    # For now, return a status message
    return {
        'success': False,
        'message': 'Active Directory integration not yet configured',
        'synced_count': 0,
        'new_users': 0,
        'updated_users': 0,
    }


def get_asset_utilization():
    """
    Calculate asset utilization metrics
    """
    from .models import Asset, DeviceStatus
    
    try:
        decommissioned_status = DeviceStatus.objects.get(name__iexact='decommissioned')
        active_assets = Asset.objects.exclude(status=decommissioned_status)
    except DeviceStatus.DoesNotExist:
        active_assets = Asset.objects.all()
    
    total_active = active_assets.count()
    
    if total_active == 0:
        return {
            'total': 0,
            'in_use': 0,
            'spare': 0,
            'utilization_rate': 0,
        }
    
    in_use = active_assets.filter(status__name__iexact='in_use').count()
    spare = active_assets.filter(status__name__iexact='spare').count()
    
    utilization_rate = (in_use / total_active * 100) if total_active > 0 else 0
    
    return {
        'total': total_active,
        'in_use': in_use,
        'spare': spare,
        'utilization_rate': round(utilization_rate, 2),
    }


def export_dashboard_data_json():
    """
    Export all dashboard data as JSON for API or download
    """
    stats = get_dashboard_stats()
    trends = get_trend_data()
    dept_analytics = get_department_analytics()
    utilization = get_asset_utilization()
    
    return {
        'generated_at': timezone.now().isoformat(),
        'statistics': stats,
        'trends': trends,
        'department_analytics': dept_analytics,
        'utilization': utilization,
    }
