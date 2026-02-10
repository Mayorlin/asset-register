from django.db import models
from django.contrib.auth.models import User
from django.forms.models import model_to_dict
from django.utils import timezone
from django.core.exceptions import ValidationError


# ---------- Reference Models ----------
class Department(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class DeviceType(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name


class DeviceStatus(models.Model):
    STATUS_SPARE = "spare"
    STATUS_IN_USE = "in-use"
    STATUS_RETRIEVED = "retrieved"
    STATUS_DECOMMISSIONED = "decommissioned"

    STATUS_CHOICES = [
        (STATUS_SPARE, "Spare"),
        (STATUS_IN_USE, "In-Use"),
        (STATUS_RETRIEVED, "Retrieved"),
        (STATUS_DECOMMISSIONED, "Decommissioned"),
    ]

    name = models.CharField(
        max_length=50,
        unique=True,
        choices=STATUS_CHOICES,
    )

    def __str__(self):
        return self.get_name_display()


class Location(models.Model):
    code = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


# ---------- Asset Model ----------
class Asset(models.Model):
    device_name = models.CharField(max_length=100)
    device_model = models.CharField(max_length=100)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    device_type = models.ForeignKey(
        DeviceType,
        on_delete=models.PROTECT
    )

    serial_number = models.CharField(
        max_length=100,
        unique=True
    )

    staff_name = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="Staff name as at time of asset assignment"
    )

    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    status = models.ForeignKey(
        DeviceStatus,
        on_delete=models.PROTECT
    )

    location = models.ForeignKey(
        Location,
        on_delete=models.PROTECT
    )
    
    def __str__(self):
        return f"{self.device_name} ({self.serial_number})"

    def clean(self):
        if not self.pk and self.status.name == "decommissioned":
            raise ValidationError(
                "You cannot assign 'Decommissioned' status during creation."
            )


# ---------- Audit Log ----------
class AuditLog(models.Model):
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name="auditlog")
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    action = models.CharField(max_length=50)
    field_name = models.CharField(max_length=100, null=True, blank=True)
    old_value = models.TextField(null=True, blank=True)
    new_value = models.TextField(null=True, blank=True)

    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.asset} - {self.action}"

    class Meta:
        ordering = ['-timestamp']


# ---------- User Profile ----------
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
        Department,
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
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'profile'):
        instance.profile.save()

