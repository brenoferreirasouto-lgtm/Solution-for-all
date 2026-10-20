from django.contrib.auth import views as auth_views

from apps.core.views import PaginaEmConstrucao

from .forms import EntrarForm


class EntrarView(auth_views.LoginView):
    template_name = "contas/entrar.html"
    authentication_form = EntrarForm
    redirect_authenticated_user = True


class SairView(auth_views.LogoutView):
    """Só aceita POST (padrão do Django 5): o botão Sair é um formulário."""


# Recuperar senha por código enviado ao e-mail (entrega #13) ----------------

class SenhaRecuperarView(PaginaEmConstrucao):
    publica = True
    titulo = "Recuperar senha"
    subtitulo = "Informe seu e-mail para receber um código."
    entrega = 13


class SenhaCodigoView(PaginaEmConstrucao):
    publica = True
    titulo = "Digite o código"
    subtitulo = "Enviamos um código de 6 dígitos para o seu e-mail."
    entrega = 13


class SenhaNovaView(PaginaEmConstrucao):
    publica = True
    titulo = "Nova senha"
    subtitulo = "Escolha uma senha nova para entrar."
    entrega = 13
