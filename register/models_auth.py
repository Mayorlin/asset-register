from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class UserProfile(models.Model):
    """
    Extended user profile with role-based permissions
    """
    ROLE_ADMIN = 'admin'
    ROLE_MANAGER = 'manager'
    ROLE_VIEWER = 'viewer'
    
    ROLE_CHOICES = [
        (ROLE_ADMIN, 'Admin'),
        (ROLE_MANAGER, 'Manager'),
        (ROLE_VIEWER, 'Viewer'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default=ROLE_VIEWER,
        help_text="Admin: Full access | Manager: Create/Edit/View | Viewer: Read-only"
    )
    phone = models.CharField(max_length=20, blank=True, null=True)
    department = models.ForeignKey(
        'Department',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="User's department"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username} ({self.get_role_display()})"
    
    @property
    def is_admin(self):
        return self.role == self.ROLE_ADMIN
    
    @property
    def is_manager(self):
        return self.role in [self.ROLE_ADMIN, self.ROLE_MANAGER]
    
    @property
    def is_viewer(self):
        return self.role == self.ROLE_VIEWER
    
    @property
    def can_create(self):
        """Can create new assets"""
        return self.role in [self.ROLE_ADMIN, self.ROLE_MANAGER]
    
    @property
    def can_edit(self):
        """Can edit existing assets"""
        return self.role in [self.ROLE_ADMIN, self.ROLE_MANAGER]
    
    @property
    def can_delete(self):
        """Can delete assets"""
        return self.role == self.ROLE_ADMIN
    
    @property
    def can_import(self):
        """Can bulk import assets"""
        return self.role == self.ROLE_ADMIN
    
    @property
    def can_export(self):
        """Can export data to CSV"""
        return True  # All users can export
    
    @property
    def can_view_audit(self):
        """Can view audit logs"""
        return self.role in [self.ROLE_ADMIN, self.ROLE_MANAGER]
    
    class Meta:
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"


# Signal to automatically create UserProfile when User is created
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'profile'):
        instance.profile.save()
