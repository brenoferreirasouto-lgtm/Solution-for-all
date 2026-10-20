"""
Quem pode acessar cada tela.

Regra do projeto: toda view diz quais papéis aceita (`papeis`). Os dados de
cada tela vêm de consultas como `Aluno.objects.visiveis_para(usuario)`, então
um professor que digitar o id de um aluno que não é dele recebe 404.
"""

from django.contrib.auth.mixins import AccessMixin
from django.core.exceptions import PermissionDenied

from apps.contas.models import Papel

TODOS = (Papel.COORDENADOR, Papel.PROFESSOR, Papel.NUCLEO)
COORDENACAO = (Papel.COORDENADOR,)
PROFESSOR = (Papel.PROFESSOR,)
GESTAO = (Papel.COORDENADOR, Papel.NUCLEO)  # enxergam todos os alunos e materiais


class PapelRequeridoMixin(AccessMixin):
    """Exige login e um dos papéis em `papeis`. Páginas com `publica = True` não exigem nada."""

    papeis = TODOS
    publica = False

    def dispatch(self, request, *args, **kwargs):
        if not self.publica:
            if not request.user.is_authenticated:
                return self.handle_no_permission()
            if request.user.papel not in self.papeis:
                raise PermissionDenied("Seu papel não tem acesso a esta tela.")
        return super().dispatch(request, *args, **kwargs)
