from django.db import migrations

def seed_locations(apps, schema_editor):
    Location = apps.get_model("register", "Location")

    locations = [
        ("HQ", "Headquarters"),
        ("YAB", "Yaba"),
        ("PH", "Port Harcourt"),
        ("ABJ", "Abuja"),
        ("ENU", "Enugu"),
        ("IBD", "Ibadan"),
        ("YOL", "Yola"),
        ("ILR", "Ilorin"),
    ]

    for code, name in locations:
        Location.objects.get_or_create(
            code=code,
            name=name
        )

class Migration(migrations.Migration):

    dependencies = [
        ("register", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_locations),
    ]
