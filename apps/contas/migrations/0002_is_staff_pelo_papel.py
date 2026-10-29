from django.db import migrations


def ajustar_is_staff(apps, schema_editor):
    """Coordenador e núcleo entram nos catálogos (/admin/); professor não."""
    Usuario = apps.get_model("contas", "Usuario")
    Usuario.objects.filter(papel__in=["COORDENADOR", "NUCLEO"]).update(is_staff=True)
    Usuario.objects.filter(papel="PROFESSOR", is_superuser=False).update(is_staff=False)


class Migration(migrations.Migration):
    dependencies = [
        ("contas", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(ajustar_is_staff, migrations.RunPython.noop),
    ]
