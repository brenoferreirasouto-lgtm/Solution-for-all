from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserChangeForm, UserCreationForm

from .models import Usuario


class UsuarioCreationForm(UserCreationForm):
    class Meta:
        model = Usuario
        fields = ("email", "nome", "papel")


class UsuarioChangeForm(UserChangeForm):
    class Meta:
        model = Usuario
        fields = ("email", "nome", "papel")


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    form = UsuarioChangeForm
    add_form = UsuarioCreationForm

    list_display = ("nome", "email", "papel", "is_active", "is_staff")
    list_filter = ("papel", "is_active", "is_staff")
    search_fields = ("nome", "email")
    ordering = ("nome",)

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Dados", {"fields": ("nome", "papel")}),
        ("Permissões", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Datas", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (None, {"classes": ("wide",), "fields": ("email", "nome", "papel", "password1", "password2")}),
    )
