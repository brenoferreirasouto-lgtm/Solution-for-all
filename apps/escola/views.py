"""
Equipe (professores e membros do núcleo) e horários das aulas.
Tudo aqui é da coordenação. Na entrega 1 são páginas "em construção".
"""

from django.contrib.auth import get_user_model

from apps.contas.models import Papel
from apps.core.permissoes import COORDENACAO
from apps.core.views import AcaoEmConstrucao, PaginaEmConstrucao

from .models import HorarioAula


class EquipeMixin:
    """Membros da equipe = professores e núcleo (o coordenador não edita outros coordenadores aqui)."""

    def get_queryset(self):
        return get_user_model().objects.filter(papel__in=[Papel.PROFESSOR, Papel.NUCLEO])


class EquipeView(PaginaEmConstrucao):
    papeis = COORDENACAO
    titulo = "Equipe"
    subtitulo = "Professores e membros do núcleo psicopedagógico."
    entrega = 4


class ProfessorNovoView(PaginaEmConstrucao):
    papeis = COORDENACAO
    titulo = "Novo professor"
    subtitulo = "Nome, e-mail, turmas, matéria e alunos acompanhados."
    entrega = 4
    voltar = "escola:equipe"


class NucleoNovoView(PaginaEmConstrucao):
    papeis = COORDENACAO
    titulo = "Novo membro do núcleo"
    subtitulo = "Nome e e-mail."
    entrega = 4
    voltar = "escola:equipe"


class MembroEditarView(EquipeMixin, PaginaEmConstrucao):
    papeis = COORDENACAO
    entrega = 4
    voltar = "escola:equipe"

    def get_titulo(self, objeto):
        return f"Editar {objeto}"


class MembroDesativarView(EquipeMixin, AcaoEmConstrucao):
    papeis = COORDENACAO
    mensagem = "Desativar acesso"
    entrega = 4
    destino = "escola:equipe"


class HorariosMixin:
    def get_queryset(self):
        return HorarioAula.objects.all()


class HorariosView(PaginaEmConstrucao):
    papeis = COORDENACAO
    titulo = "Horários das aulas"
    subtitulo = "Grade semanal por turma. Alimenta o card \"Aulas de hoje\"."
    entrega = 6


class HorarioNovoView(PaginaEmConstrucao):
    papeis = COORDENACAO
    titulo = "Novo horário"
    entrega = 6
    voltar = "escola:horarios"


class HorarioEditarView(HorariosMixin, PaginaEmConstrucao):
    papeis = COORDENACAO
    entrega = 6
    voltar = "escola:horarios"

    def get_titulo(self, objeto):
        return f"Editar horário: {objeto}"


class HorarioExcluirView(HorariosMixin, AcaoEmConstrucao):
    papeis = COORDENACAO
    mensagem = "Excluir horário"
    entrega = 6
    destino = "escola:horarios"
