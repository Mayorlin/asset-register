from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from .decorators import admin_required, manager_required
from .utils_dashboard import (
    get_dashboard_stats,
    get_trend_data,
    get_department_analytics,
    search_ad_users,
    get_asset_utilization,
    export_dashboard_data_json
)
from .models_dashboard import ADUser, AssetMetrics
from .models import Asset, Department, DeviceType, Location
from datetime import date
import json


@login_required
def dashboard(request):
    """
    Main dashboard view with statistics and charts
    """
    stats = get_dashboard_stats()
    utilization = get_asset_utilization()
    
    # Get trend data for the last 30 days
    trends = get_trend_data(days=30)
    
    context = {
        'stats': stats,
        'utilization': utilization,
        'trends': trends,
        'page_title': 'Dashboard',
    }
    
    return render(request, 'register/dashboard/dashboard.html', context)


@login_required
def analytics(request):
    """
    Detailed analytics view with department breakdown
    """
    dept_analytics = get_department_analytics()
    trends = get_trend_data(days=90)  # 3 months
    
    context = {
        'department_analytics': dept_analytics,
        'trends': trends,
        'page_title': 'Analytics',
    }
    
    return render(request, 'register/dashboard/analytics.html', context)


@login_required
@require_http_methods(["GET"])
def api_dashboard_stats(request):
    """
    API endpoint for dashboard statistics (for AJAX updates)
    """
    stats = get_dashboard_stats()
    return JsonResponse(stats, safe=False)


@login_required
@require_http_methods(["GET"])
def api_chart_data(request):
    """
    API endpoint for chart data
    """
    chart_type = request.GET.get('type', 'status')
    stats = get_dashboard_stats()
    
    if chart_type == 'status':
        data = {
            'labels': [item['status__name'] for item in stats['status_breakdown']],
            'values': [item['count'] for item in stats['status_breakdown']],
        }
    elif chart_type == 'device_type':
        data = {
            'labels': [item['device_type__name'] for item in stats['device_type_breakdown']],
            'values': [item['count'] for item in stats['device_type_breakdown']],
        }
    elif chart_type == 'department':
        data = {
            'labels': [item['department__name'] or 'Unassigned' for item in stats['department_breakdown']],
            'values': [item['count'] for item in stats['department_breakdown']],
        }
    elif chart_type == 'location':
        data = {
            'labels': [item['location__name'] for item in stats['location_breakdown']],
            'values': [item['count'] for item in stats['location_breakdown']],
        }
    elif chart_type == 'trends':
        trends = get_trend_data(days=30)
        data = {
            'created': trends['created_trend'],
            'updated': trends['updated_trend'],
        }
    else:
        data = {'error': 'Invalid chart type'}
    
    return JsonResponse(data)


@login_required
@require_http_methods(["GET"])
def api_search_users(request):
    """
    API endpoint to search for AD users for asset assignment
    """
    query = request.GET.get('q', '')
    users = search_ad_users(query)
    return JsonResponse({'users': users})


@admin_required
def ad_user_management(request):
    """
    Manage AD users (view, add manually, sync from AD)
    """
    users = ADUser.objects.select_related('department', 'office_location').all()
    
    context = {
        'ad_users': users,
        'total_users': users.count(),
        'active_users': users.filter(is_active=True).count(),
        'ad_synced_users': users.filter(is_from_ad=True).count(),
        'page_title': 'AD User Management',
    }
    
    return render(request, 'register/dashboard/ad_user_management.html', context)


@admin_required
@require_http_methods(["POST"])
def ad_user_create(request):
    """
    Manually create an AD user entry
    """
    from django.contrib import messages
    from django.shortcuts import redirect
    
    username = request.POST.get('username')
    email = request.POST.get('email')
    first_name = request.POST.get('first_name', '')
    last_name = request.POST.get('last_name', '')
    display_name = request.POST.get('display_name', '')
    employee_id = request.POST.get('employee_id', '')
    job_title = request.POST.get('job_title', '')
    phone = request.POST.get('phone', '')
    
    dept_id = request.POST.get('department')
    location_id = request.POST.get('office_location')
    
    # Validate
    if not username:
        messages.error(request, "Username is required")
        return redirect('ad_user_management')
    
    if ADUser.objects.filter(username=username).exists():
        messages.error(request, f"User '{username}' already exists")
        return redirect('ad_user_management')
    
    # Create user
    ad_user = ADUser.objects.create(
        username=username,
        email=email,
        first_name=first_name,
        last_name=last_name,
        display_name=display_name or f"{first_name} {last_name}".strip(),
        employee_id=employee_id,
        job_title=job_title,
        phone=phone,
        is_from_ad=False,  # Manually created
    )
    
    if dept_id:
        ad_user.department = Department.objects.get(id=dept_id)
    
    if location_id:
        ad_user.office_location = Location.objects.get(id=location_id)
    
    ad_user.save()
    
    messages.success(request, f"User '{username}' created successfully")
    return redirect('ad_user_management')


@admin_required
def generate_metrics(request):
    """
    Generate metrics snapshot for today
    """
    from django.contrib import messages
    from django.shortcuts import redirect
    
    today = date.today()
    metrics = AssetMetrics.generate_for_date(today)
    
    messages.success(request, f"Metrics generated for {today}")
    return redirect('dashboard')


@login_required
def export_dashboard_json(request):
    """
    Export complete dashboard data as JSON
    """
    from django.http import JsonResponse
    
    data = export_dashboard_data_json()
    
    return JsonResponse(data, json_dumps_params={'indent': 2})
