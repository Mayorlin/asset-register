from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required


def role_required(*roles):
    """
    Decorator to check if user has one of the specified roles.
    Usage: @role_required('admin', 'manager')
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapper(request, *args, **kwargs):
            if not hasattr(request.user, 'profile'):
                messages.error(request, "User profile not found. Please contact administrator.")
                return redirect('asset_list')
            
            if request.user.profile.role in roles:
                return view_func(request, *args, **kwargs)
            else:
                messages.error(request, "You don't have permission to access this page.")
                return redirect('asset_list')
        return wrapper
    return decorator


def admin_required(view_func):
    """
    Decorator to restrict access to Admin users only
    """
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not hasattr(request.user, 'profile'):
            messages.error(request, "User profile not found. Please contact administrator.")
            return redirect('asset_list')
        
        if request.user.profile.is_admin:
            return view_func(request, *args, **kwargs)
        else:
            messages.error(request, "Admin access required for this action.")
            return redirect('asset_list')
    return wrapper


def manager_required(view_func):
    """
    Decorator to restrict access to Manager and Admin users
    """
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not hasattr(request.user, 'profile'):
            messages.error(request, "User profile not found. Please contact administrator.")
            return redirect('asset_list')
        
        if request.user.profile.is_manager:
            return view_func(request, *args, **kwargs)
        else:
            messages.error(request, "Manager or Admin access required for this action.")
            return redirect('asset_list')
    return wrapper


def can_create_asset(view_func):
    """
    Decorator to check if user can create assets
    """
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not hasattr(request.user, 'profile'):
            messages.error(request, "User profile not found. Please contact administrator.")
            return redirect('asset_list')
        
        if request.user.profile.can_create:
            return view_func(request, *args, **kwargs)
        else:
            messages.error(request, "You don't have permission to create assets.")
            return redirect('asset_list')
    return wrapper


def can_edit_asset(view_func):
    """
    Decorator to check if user can edit assets
    """
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not hasattr(request.user, 'profile'):
            messages.error(request, "User profile not found. Please contact administrator.")
            return redirect('asset_list')
        
        if request.user.profile.can_edit:
            return view_func(request, *args, **kwargs)
        else:
            messages.error(request, "You don't have permission to edit assets.")
            return redirect('asset_list')
    return wrapper


def can_delete_asset(view_func):
    """
    Decorator to check if user can delete assets
    """
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not hasattr(request.user, 'profile'):
            messages.error(request, "User profile not found. Please contact administrator.")
            return redirect('asset_list')
        
        if request.user.profile.can_delete:
            return view_func(request, *args, **kwargs)
        else:
            messages.error(request, "Only admins can delete assets.")
            return redirect('asset_list')
    return wrapper


def can_import_assets(view_func):
    """
    Decorator to check if user can bulk import assets
    """
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not hasattr(request.user, 'profile'):
            messages.error(request, "User profile not found. Please contact administrator.")
            return redirect('asset_list')
        
        if request.user.profile.can_import:
            return view_func(request, *args, **kwargs)
        else:
            messages.error(request, "Only admins can import assets.")
            return redirect('asset_list')
    return wrapper


def can_view_audit(view_func):
    """
    Decorator to check if user can view audit logs
    """
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not hasattr(request.user, 'profile'):
            messages.error(request, "User profile not found. Please contact administrator.")
            return redirect('asset_list')
        
        if request.user.profile.can_view_audit:
            return view_func(request, *args, **kwargs)
        else:
            messages.error(request, "You don't have permission to view audit logs.")
            return redirect('asset_list')
    return wrapper
