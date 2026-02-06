from django.contrib import admin
from .models import Department, DeviceType, DeviceStatus, Location, Asset

# Register your models here.
admin.site.register(Department)
admin.site.register(DeviceType)
admin.site.register(DeviceStatus)
admin.site.register(Asset)

@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ("code", "name")
    search_fields = ("code", "name")
