import csv
from django.shortcuts import get_object_or_404, render, redirect
from django.http import HttpResponse
from .models import Asset, DeviceStatus, DeviceType, AuditLog, Department, Location
from .forms import AssetForm
from django.db import transaction
from django.contrib import messages
from .utils import filter_assets, log_asset_action
from django.core.paginator import Paginator
from django.forms.models import model_to_dict
from .utils import export_assets_to_csv
from django.utils.timezone import now
from io import TextIOWrapper
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from .decorators import (
    can_create_asset, 
    can_edit_asset, 
    can_delete_asset, 
    can_import_assets,
    can_view_audit,
    admin_required,
    manager_required
)


# ---------- Asset List ----------
@login_required
def asset(request):
    serial_number = request.GET.get("serial_number")
    device_status = request.GET.get("device_status")
    device_type = request.GET.get("device_type")
    staff_name = request.GET.get("staff_name")

    # Exclude decommissioned assets
    try:
        decommissioned_status = DeviceStatus.objects.get(name__iexact="decommissioned")
    except DeviceStatus.DoesNotExist:
        decommissioned_status = None

    assets = Asset.objects.select_related(
        "status", "device_type", "department", "location"
    ).all()

    if decommissioned_status:
        assets = assets.exclude(status=decommissioned_status)

    # Filters
    if serial_number:
        assets = assets.filter(serial_number__icontains=serial_number)

    if device_status:
        assets = assets.filter(status_id=device_status)

    if device_type:
        assets = assets.filter(device_type_id=device_type)

    if staff_name:
        assets = assets.filter(staff_name__icontains=staff_name)

    # Pagination
    paginator = Paginator(assets, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(request, "register/asset.html", {
        "assets": page_obj,
        "statuses": DeviceStatus.objects.exclude(name__iexact="decommissioned"),
        "device_types": DeviceType.objects.all(),
        "page_obj": page_obj,
    })
    

@login_required
def asset_history(request, pk):
    # Get the asset
    asset = get_object_or_404(Asset, pk=pk)
    
    # Get all audit log entries for this asset, ordered by timestamp
    history = AuditLog.objects.filter(asset=asset).order_by("timestamp")
    
    return render(request, "register/asset_history.html", {
        "history": history,
        "asset": asset
    })
    

@login_required
def decommissioned_assets(request):
    try:
        decommissioned_status = DeviceStatus.objects.get(name__iexact="decommissioned")
    except DeviceStatus.DoesNotExist:
        decommissioned_status = None

    if decommissioned_status:
        assets = Asset.objects.filter(status=decommissioned_status).select_related(
            "status", "device_type", "department", "location"
        )
    else:
        assets = Asset.objects.none()

    # Filtering
    serial_number = request.GET.get("serial_number")
    device_type = request.GET.get("device_type")
    staff_name = request.GET.get("staff_name")

    if serial_number:
        assets = assets.filter(serial_number__icontains=serial_number)
    if device_type:
        assets = assets.filter(device_type_id=device_type)
    if staff_name:
        assets = assets.filter(staff_name__icontains=staff_name)

    # Pagination
    paginator = Paginator(assets, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(request, "register/decommissioned_assets.html", {
        "assets": page_obj,
        "statuses": DeviceStatus.objects.all(),
        "device_types": DeviceType.objects.all(),
        "page_obj": page_obj,
    })


@can_view_audit
def audit_overview(request):
    logs = AuditLog.objects.select_related("asset", "user").order_by("-timestamp")

    # Optional filters (user, asset) can be added here later

    paginator = Paginator(logs, 20)  # 20 entries per page
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(request, "register/audit_overview.html", {
        "page_obj": page_obj
    })


@can_create_asset
def asset_create(request):
    if request.method == "POST":
        form = AssetForm(request.POST)
        if form.is_valid():
            asset = form.save(commit=False)
            asset.save()

            # LOG CREATION
            log_asset_action(
                user=request.user,
                asset=asset,
                action="created",
                field_name="asset",
                old_value="",
                new_value="Asset created"
            )

            messages.success(request, "Asset created successfully.")
            return redirect("asset_list")

    else:
        form = AssetForm()

    return render(request, "register/asset_form.html", {
        "form": form,
        "is_update": False,
    })


@can_import_assets
def import_assets(request):
    if request.method == "POST":
        csv_file = request.FILES.get("csv_file")

        if not csv_file or not csv_file.name.endswith(".csv"):
            messages.error(request, "Please upload a valid CSV file.")
            return redirect("import_assets")

        decoded = csv_file.read().decode("utf-8").splitlines()
        reader = csv.DictReader(decoded)

        required_headers = {
            "Device Name",
            "Device Model",
            "Serial Number",
            "Device Type",
            "Status",
            "Location",
            "Staff Name",
        }

        if not required_headers.issubset(reader.fieldnames):
            missing = required_headers - set(reader.fieldnames)
            messages.error(
                request,
                f"Invalid CSV format. Missing required columns: {', '.join(missing)}. Use exported CSV as template."
            )
            return redirect("import_assets")

        valid_rows = []
        error_rows = []

        decommissioned_status = DeviceStatus.objects.filter(
            name__iexact="decommissioned"
        ).first()

        for index, row in enumerate(reader, start=2):
            row_errors = []
            serial = row["Serial Number"].strip()

            # Validate serial number uniqueness
            if Asset.objects.filter(serial_number=serial).exists():
                row_errors.append(f"Serial number '{serial}' already exists in the system")

            # Validate device type
            device_type = DeviceType.objects.filter(
                name__iexact=row["Device Type"].strip()
            ).first()
            if not device_type:
                row_errors.append(f"Invalid device type '{row['Device Type']}'")

            # Validate status
            status = DeviceStatus.objects.filter(
                name__iexact=row["Status"].strip()
            ).first()
            if not status:
                row_errors.append(f"Invalid status '{row['Status']}'")
            elif decommissioned_status and status == decommissioned_status:
                row_errors.append("Cannot import assets with 'decommissioned' status")

            # Validate location
            location = Location.objects.filter(
                name__iexact=row["Location"].strip()
            ).first()
            if not location:
                row_errors.append(f"Invalid location '{row['Location']}'")

            # Validate department (optional)
            department = None
            dept_value = row.get("Department", "").strip()
            if dept_value:
                department = Department.objects.filter(
                    name__iexact=dept_value
                ).first()
                if not department:
                    row_errors.append(f"Invalid department '{dept_value}'")

            # If there are errors, add to error_rows
            if row_errors:
                error_rows.append({
                    "row_number": index,
                    "device_name": row.get("Device Name", "").strip(),
                    "device_model": row.get("Device Model", "").strip(),
                    "serial_number": serial,
                    "device_type": row.get("Device Type", "").strip(),
                    "status": row.get("Status", "").strip(),
                    "location": row.get("Location", "").strip(),
                    "department": dept_value,
                    "staff_name": row.get("Staff Name", "").strip(),
                    "errors": row_errors,
                })
            else:
                # No errors, add to valid rows
                valid_rows.append({
                    "row_number": index,
                    "device_name": row["Device Name"].strip(),
                    "device_model": row["Device Model"].strip(),
                    "serial_number": serial,
                    "device_type": device_type.name,
                    "status": status.name,
                    "location": location.name,
                    "department": department.name if department else "",
                    "staff_name": row["Staff Name"].strip(),
                })

        request.session["import_rows"] = valid_rows

        return render(
            request,
            "register/import_preview.html",
            {
                "valid_rows": valid_rows,
                "error_rows": error_rows,
            }
        )

    return render(request, "register/import_assets.html")


@can_import_assets
def confirm_import(request):
    rows = request.session.get("import_rows")

    if not rows:
        messages.error(request, "No import data found.")
        return redirect("import_assets")

    assets = []

    with transaction.atomic():
        for row in rows:
            # Get department if provided
            department = None
            if row.get("department"):
                department = Department.objects.get(name=row["department"])

            asset = Asset.objects.create(
                device_name=row["device_name"],
                device_model=row["device_model"],
                serial_number=row["serial_number"],
                device_type=DeviceType.objects.get(name=row["device_type"]),
                status=DeviceStatus.objects.get(name=row["status"]),
                location=Location.objects.get(name=row["location"]),
                department=department,
                staff_name=row["staff_name"],
            )

            log_asset_action(
                user=request.user,
                asset=asset,
                action="import",
                field_name="asset",
                old_value="",
                new_value="Asset imported via CSV"
            )

            assets.append(asset)

    del request.session["import_rows"]

    messages.success(
        request, f"{len(assets)} assets imported successfully."
    )

    return redirect("asset_list")


@can_edit_asset
def asset_update(request, pk):
    asset = get_object_or_404(Asset, pk=pk)
    old_asset = Asset.objects.get(pk=pk)

    if request.method == "POST":
        form = AssetForm(request.POST, instance=asset)

        if form.is_valid():
            updated_asset = form.save()

            tracked_fields = [
                "device_name",
                "device_model",
                "status",
                "location",
                "department",
                "staff_name",
            ]

            for field in tracked_fields:
                old_value = getattr(old_asset, field)
                new_value = getattr(updated_asset, field)

                if old_value != new_value:
                    log_asset_action(
                        user=request.user,
                        asset=updated_asset,
                        action="updated",
                        field_name=field,
                        old_value=str(old_value),
                        new_value=str(new_value)
                    )

            messages.success(request, "Asset updated successfully.")
            return redirect("asset_list")

    else:
        form = AssetForm(instance=asset)

    return render(request, "register/asset_form.html", {
        "form": form,
        "is_update": True,
    })    


# ---------- CSV Export ----------
@login_required
def export_assets_csv(request):
    assets = Asset.objects.exclude(
        status__name__iexact="decommissioned"
    )

    assets = filter_assets(request, assets)

    return export_assets_to_csv(assets)


@login_required
def export_decommissioned_assets_csv(request):
    try:
        decommissioned_status = DeviceStatus.objects.get(
            name__iexact="decommissioned"
        )
    except DeviceStatus.DoesNotExist:
        return export_assets_to_csv(Asset.objects.none())

    assets = Asset.objects.filter(
        status=decommissioned_status
    ).select_related(
        "device_type", "status", "location", "department"
    )

    return export_assets_to_csv(assets)


@can_view_audit
def system_history(request):
    logs = (
        AuditLog.objects
        .select_related("user", "asset")
        .order_by("-timestamp")
    )

    paginator = Paginator(logs, 20)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(request, "register/system_history.html", {
        "page_obj": page_obj
    })
