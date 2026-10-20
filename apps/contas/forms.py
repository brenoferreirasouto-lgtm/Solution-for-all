from django import forms
from django.contrib.auth.forms import AuthenticationForm


class EntrarForm(AuthenticationForm):
    """Login por e-mail e senha. O papel vem do banco, não da tela."""

    username = forms.EmailField(
        label="E-mail",
        widget=forms.EmailInput(attrs={"autofocus": True, "autocomplete": "email", "placeholder": "voce@escola.com"}),
    )
    password = forms.CharField(
        label="Senha",
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "current-password"}),
    )

    error_messages = {
        "invalid_login": "E-mail ou senha incorretos.",
        "inactive": "Este acesso foi desativado pela coordenação.",
    }
