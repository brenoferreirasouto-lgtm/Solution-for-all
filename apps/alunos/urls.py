from django.urls import path

from . import views

app_name = "alunos"

urlpatterns = [
    path("", views.AlunoListaView.as_view(), name="lista"),
    path("novo/", views.AlunoNovoView.as_view(), name="novo"),
    path("<int:pk>/", views.AlunoDetalheView.as_view(), name="detalhe"),
    path("<int:pk>/editar/", views.AlunoEditarView.as_view(), name="editar"),
    path("<int:pk>/arquivar/", views.AlunoArquivarView.as_view(), name="arquivar"),
]
