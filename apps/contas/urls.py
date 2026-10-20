from django.urls import path

from . import views

app_name = "contas"

urlpatterns = [
    path("entrar/", views.EntrarView.as_view(), name="entrar"),
    path("sair/", views.SairView.as_view(), name="sair"),
    path("senha/recuperar/", views.SenhaRecuperarView.as_view(), name="senha_recuperar"),
    path("senha/codigo/", views.SenhaCodigoView.as_view(), name="senha_codigo"),
    path("senha/nova/", views.SenhaNovaView.as_view(), name="senha_nova"),
]
