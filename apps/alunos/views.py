"""
Telas de alunos. Na entrega 1 são páginas "em construção".

Professor vê só os alunos vinculados a ele; coordenação e núcleo veem todos.
Cadastrar, editar e arquivar é só da coordenação.
"""

from apps.core.permissoes import COORDENACAO, TODOS
from apps.core.views import AcaoEmConstrucao, PaginaEmConstrucao

from .models import Aluno


class AlunosVisiveisMixin:
    def get_queryset(self):
        return Aluno.objects.visiveis_para(self.request.user)


class AlunoListaView(PaginaEmConstrucao):
    papeis = TODOS
    titulo = "Alunos"
    subtitulo = "Busca por nome (?q=) e filtro por necessidade (?necessidade=tea)."
    entrega = 10


class AlunoNovoView(PaginaEmConstrucao):
    papeis = COORDENACAO
    titulo = "Novo aluno"
    subtitulo = "Nome, turma, necessidades, formatos recomendados e professores."
    entrega = 5
    voltar = "alunos:lista"


class AlunoDetalheView(AlunosVisiveisMixin, PaginaEmConstrucao):
    papeis = TODOS
    subtitulo = "Perfil do aluno e histórico de adaptações."
    entrega = 5
    voltar = "alunos:lista"


class AlunoEditarView(AlunosVisiveisMixin, PaginaEmConstrucao):
    papeis = COORDENACAO
    subtitulo = "Editar perfil do aluno."
    entrega = 5
    voltar = "alunos:lista"

    def get_titulo(self, objeto):
        return f"Editar {objeto}"


class AlunoArquivarView(AlunosVisiveisMixin, AcaoEmConstrucao):
    papeis = COORDENACAO
    mensagem = "Arquivar aluno"
    entrega = 5
    destino = "alunos:detalhe"
    destino_com_pk = True
