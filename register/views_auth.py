from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from .models import UserProfile, Department
from .decorators import admin_required
from django.db import transaction


def user_login(request):
    """
    User login view
    """
    if request.user.is_authenticated:
        return redirect('asset_list')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, f"Welcome back, {user.get_full_name() or user.username}!")
            
            # Redirect to next page if specified, otherwise to asset list
            next_page = request.GET.get('next', 'asset_list')
            return redirect(next_page)
        else:
            messages.error(request, "Invalid username or password.")
    
    return render(request, 'register/auth/login.html')


@login_required
def user_logout(request):
    """
    User logout view
    """
    logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect('login')


@login_required
def user_profile(request):
    """
    View and edit user profile
    """
    profile = request.user.profile
    
    if request.method == 'POST':
        # Update user information
        request.user.first_name = request.POST.get('first_name', '')
        request.user.last_name = request.POST.get('last_name', '')
        request.user.email = request.POST.get('email', '')
        request.user.save()
        
        # Update profile
        profile.phone = request.POST.get('phone', '')
        
        dept_id = request.POST.get('department')
        if dept_id:
            profile.department = Department.objects.get(id=dept_id)
        else:
            profile.department = None
        
        profile.save()
        
        messages.success(request, "Profile updated successfully.")
        return redirect('user_profile')
    
    return render(request, 'register/auth/profile.html', {
        'profile': profile,
        'departments': Department.objects.all(),
    })


@login_required
def change_password(request):
    """
    Change user password
    """
    if request.method == 'POST':
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        
        # Verify current password
        if not request.user.check_password(current_password):
            messages.error(request, "Current password is incorrect.")
            return redirect('change_password')
        
        # Check if new passwords match
        if new_password != confirm_password:
            messages.error(request, "New passwords do not match.")
            return redirect('change_password')
        
        # Check password length
        if len(new_password) < 8:
            messages.error(request, "Password must be at least 8 characters long.")
            return redirect('change_password')
        
        # Change password
        request.user.set_password(new_password)
        request.user.save()
        
        # Re-login the user
        user = authenticate(username=request.user.username, password=new_password)
        login(request, user)
        
        messages.success(request, "Password changed successfully.")
        return redirect('user_profile')
    
    return render(request, 'register/auth/change_password.html')


@admin_required
def user_management(request):
    """
    Admin view to manage users and their roles
    """
    users = User.objects.select_related('profile').all().order_by('username')
    
    return render(request, 'register/auth/user_management.html', {
        'users': users,
    })


@admin_required
def user_create(request):
    """
    Admin view to create new users
    """
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        password = request.POST.get('password')
        role = request.POST.get('role', 'viewer')
        phone = request.POST.get('phone', '')
        dept_id = request.POST.get('department')
        
        # Validate username
        if User.objects.filter(username=username).exists():
            messages.error(request, f"Username '{username}' already exists.")
            return redirect('user_create')
        
        # Validate password
        if len(password) < 8:
            messages.error(request, "Password must be at least 8 characters long.")
            return redirect('user_create')
        
        with transaction.atomic():
            # Create user
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name
            )
            
            # Update profile
            profile = user.profile
            profile.role = role
            profile.phone = phone
            
            if dept_id:
                profile.department = Department.objects.get(id=dept_id)
            
            profile.save()
        
        messages.success(request, f"User '{username}' created successfully.")
        return redirect('user_management')
    
    return render(request, 'register/auth/user_create.html', {
        'departments': Department.objects.all(),
        'role_choices': UserProfile.ROLE_CHOICES,
    })


@admin_required
def user_edit(request, user_id):
    """
    Admin view to edit user details and role
    """
    user = get_object_or_404(User, id=user_id)
    profile = user.profile
    
    if request.method == 'POST':
        user.email = request.POST.get('email', '')
        user.first_name = request.POST.get('first_name', '')
        user.last_name = request.POST.get('last_name', '')
        user.is_active = request.POST.get('is_active') == 'on'
        user.save()
        
        # Update profile
        profile.role = request.POST.get('role', 'viewer')
        profile.phone = request.POST.get('phone', '')
        
        dept_id = request.POST.get('department')
        if dept_id:
            profile.department = Department.objects.get(id=dept_id)
        else:
            profile.department = None
        
        profile.save()
        
        messages.success(request, f"User '{user.username}' updated successfully.")
        return redirect('user_management')
    
    return render(request, 'register/auth/user_edit.html', {
        'edit_user': user,
        'profile': profile,
        'departments': Department.objects.all(),
        'role_choices': UserProfile.ROLE_CHOICES,
    })


@admin_required
def user_delete(request, user_id):
    """
    Admin view to delete a user
    """
    user = get_object_or_404(User, id=user_id)
    
    # Prevent deleting own account
    if user == request.user:
        messages.error(request, "You cannot delete your own account.")
        return redirect('user_management')
    
    if request.method == 'POST':
        username = user.username
        user.delete()
        messages.success(request, f"User '{username}' deleted successfully.")
        return redirect('user_management')
    
    return render(request, 'register/auth/user_delete.html', {
        'delete_user': user,
    })


@admin_required
def user_reset_password(request, user_id):
    """
    Admin view to reset user password
    """
    user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        
        if new_password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return redirect('user_reset_password', user_id=user_id)
        
        if len(new_password) < 8:
            messages.error(request, "Password must be at least 8 characters long.")
            return redirect('user_reset_password', user_id=user_id)
        
        user.set_password(new_password)
        user.save()
        
        messages.success(request, f"Password reset successfully for '{user.username}'.")
        return redirect('user_management')
    
    return render(request, 'register/auth/user_reset_password.html', {
        'reset_user': user,
    })
