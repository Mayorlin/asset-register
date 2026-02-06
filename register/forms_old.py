from django import forms
from .models import Asset

class AssetForm(forms.ModelForm):
    class Meta:
        model = Asset
        fields = [
            "device_name",
            "device_model",
            "serial_number",
            "device_type",
            "status",
            "location",
            "department",
            "staff_name",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Make serial number readonly after creation
        if self.instance and self.instance.pk:
            self.fields['serial_number'].disabled = True

        # Optional: prevent new asset from being created with decommissioned status
        if not self.instance.pk:
            self.fields["status"].queryset = (self.fields["status"].queryset.exclude(name="decommissioned"))

