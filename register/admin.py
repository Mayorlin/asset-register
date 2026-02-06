from django.contrib import admin
from .models import Department, DeviceType, DeviceStatus, Location, Asset, UserProfile

# Register your models here.
admin.site.register(Department)
admin.site.register(DeviceType)
admin.site.register(DeviceStatus)
admin.site.register(Asset)

@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ("code", "name")
    search_fields = ("code", "name")

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "role", "department", "phone", "created_at")
    list_filter = ("role", "department")
    search_fields = ("user__username", "user__email", "user__first_name", "user__last_name")
    readonly_fields = ("created_at", "updated_at")
