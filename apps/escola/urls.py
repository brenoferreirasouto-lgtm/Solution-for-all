from django.urls import path

from . import views

app_name = "escola"

urlpatterns = [
    path("equipe/", views.EquipeView.as_view(), name="equipe"),
    path("equipe/coordenadores/novo/", views.CoordenadorNovoView.as_view(), name="coordenador_novo"),
    path("equipe/professores/novo/", views.ProfessorNovoView.as_view(), name="professor_novo"),
    path("equipe/nucleo/novo/", views.NucleoNovoView.as_view(), name="nucleo_novo"),
    path("equipe/<int:pk>/editar/", views.MembroEditarView.as_view(), name="membro_editar"),
    path("equipe/<int:pk>/desativar/", views.MembroDesativarView.as_view(), name="membro_desativar"),
    path("horarios/", views.HorariosView.as_view(), name="horarios"),
    path("horarios/novo/", views.HorarioNovoView.as_view(), name="horario_novo"),
    path("horarios/<int:pk>/editar/", views.HorarioEditarView.as_view(), name="horario_editar"),
    path("horarios/<int:pk>/excluir/", views.HorarioExcluirView.as_view(), name="horario_excluir"),
]
