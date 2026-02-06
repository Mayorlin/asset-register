from django import forms
from .models import Asset

class AssetForm(forms.ModelForm):
    # Enhanced staff_name field with autocomplete
    staff_name = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Type to search users...',
            'autocomplete': 'off',
            'id': 'staff_name_autocomplete',
            'list': 'user_suggestions'
        }),
        help_text="Start typing to search for users from Active Directory"
    )
    
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
            self.fields["status"].queryset = (
                self.fields["status"].queryset.exclude(name="decommissioned")
            )
        
        # Add CSS classes to all fields
        for field_name, field in self.fields.items():
            if 'class' not in field.widget.attrs:
                field.widget.attrs['class'] = 'form-control'
