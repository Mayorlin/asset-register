import csv
from django.http import HttpResponse

def filter_assets(request, queryset):
    serial_number = request.GET.get("serial_number")
    device_status = request.GET.get("device_status")
    device_type = request.GET.get("device_type")
    staff_name = request.GET.get("staff_name")

    if serial_number:
        queryset = queryset.filter(serial_number__icontains=serial_number)

    if device_status:
        queryset = queryset.filter(status_id=device_status)

    if device_type:
        queryset = queryset.filter(device_type_id=device_type)

    if staff_name:
        queryset = queryset.filter(staff_name__icontains=staff_name)

    return queryset

def log_asset_action(user, asset, action, field_name=None, old_value=None, new_value=None):
    """
    Logs an action performed on an asset.
    :param user: User performing the action
    :param asset: Asset instance
    :param action: String: 'created', 'updated', 'import', 'decommissioned', etc.
    :param field_name: Optional field name that was changed
    :param old_value: Optional old value
    :param new_value: Optional new value
    """
    from .models import AuditLog
    AuditLog.objects.create(
        user=user,
        asset=asset,
        action=action,
        field_name=field_name,
        old_value=old_value,
        new_value=new_value
    )
    
def export_assets_to_csv(queryset):
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="assets.csv"'

    writer = csv.writer(response)
    writer.writerow([
        "Device Name",
        "Device Model",
        "Serial Number",
        "Device Type",
        "Status",
        "Location",
        "Department",
        "Staff Name",
        "Date Modified",
    ])

    for asset in queryset:
        writer.writerow([
            asset.device_name,
            asset.device_model,
            asset.serial_number,
            asset.device_type.name if asset.device_type else "",
            asset.status.name if asset.status else "",
            asset.location.name if asset.location else "",
            asset.department.name if asset.department else "",
            asset.staff_name,
            asset.updated_at.strftime("%Y-%m-%d %H:%M") if asset.updated_at else "",
        ])

    return response
