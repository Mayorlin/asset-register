from django.urls import path
from . import views
from .views_auth import (
    user_login,
    user_logout,
    user_profile,
    change_password,
    user_management,
    user_create,
    user_edit,
    user_delete,
    user_reset_password,
)
from .views_dashboard import (
    dashboard,
    analytics,
    api_dashboard_stats,
    api_chart_data,
    api_search_users,
    ad_user_management,
    ad_user_create,
    export_dashboard_json,
)

urlpatterns = [
    # Dashboard URLs
    path('', dashboard, name='dashboard'),
    path('dashboard/', dashboard, name='dashboard'),
    path('analytics/', analytics, name='analytics'),
    
    # API endpoints
    path('api/dashboard-stats/', api_dashboard_stats, name='api_dashboard_stats'),
    path('api/chart-data/', api_chart_data, name='api_chart_data'),
    path('api/search-users/', api_search_users, name='api_search_users'),
    path('export/dashboard-json/', export_dashboard_json, name='export_dashboard_json'),
    
    # AD User Management
    path('ad-users/', ad_user_management, name='ad_user_management'),
    path('ad-users/create/', ad_user_create, name='ad_user_create'),
    
    # Authentication URLs
    path('login/', user_login, name='login'),
    path('logout/', user_logout, name='logout'),
    path('profile/', user_profile, name='user_profile'),
    path('change-password/', change_password, name='change_password'),
    
    # User Management (Admin only)
    path('users/', user_management, name='user_management'),
    path('users/create/', user_create, name='user_create'),
    path('users/<int:user_id>/edit/', user_edit, name='user_edit'),
    path('users/<int:user_id>/delete/', user_delete, name='user_delete'),
    path('users/<int:user_id>/reset-password/', user_reset_password, name='user_reset_password'),
    
    # Asset URLs
    path('assets/', views.asset, name='asset_list'),
    path("assets/new/", views.asset_create, name="asset_create"),
    path("assets/<int:pk>/edit/", views.asset_update, name="asset_update"),
    path('assets/<int:pk>/history/', views.asset_history, name='asset_history'),
    path('assets/export/', views.export_assets_csv, name='export_assets_csv'),
    path('assets/decommissioned/', views.decommissioned_assets, name='decommissioned_assets'),
    path('assets/decommissioned/export/', views.export_decommissioned_assets_csv, name='export_decommissioned_assets_csv'),
    path("history/", views.system_history, name="system_history"),
    path("assets/import/", views.import_assets, name="import_assets"),
    path("assets/import/confirm/", views.confirm_import, name="confirm_import"),
]
