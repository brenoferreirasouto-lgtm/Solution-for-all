from django.urls import path

from . import views

app_name = "materiais"

urlpatterns = [
    path("materiais/", views.MaterialListaView.as_view(), name="lista"),
    path("materiais/adaptar/", views.AdaptarView.as_view(), name="adaptar"),
    path("materiais/<int:pk>/", views.MaterialDetalheView.as_view(), name="detalhe"),
    path("adaptacoes/<int:pk>/", views.AdaptacaoDetalheView.as_view(), name="adaptacao"),
    path("adaptacoes/<int:pk>/refazer/", views.AdaptacaoRefazerView.as_view(), name="adaptacao_refazer"),
    path("adaptacoes/<int:pk>/exportar/", views.AdaptacaoExportarView.as_view(), name="adaptacao_exportar"),
]
