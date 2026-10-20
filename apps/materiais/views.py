"""
Materiais e adaptações. Na entrega 1 são páginas "em construção".

Professor vê os materiais que enviou e as adaptações dos alunos dele;
coordenação e núcleo veem tudo. Só o professor adapta material.
"""

from django.urls import reverse

from apps.core.permissoes import PROFESSOR, TODOS
from apps.core.views import AcaoEmConstrucao, PaginaEmConstrucao

from .models import Adaptacao, Material


class MateriaisVisiveisMixin:
    def get_queryset(self):
        return Material.objects.visiveis_para(self.request.user)


class AdaptacoesVisiveisMixin:
    def get_queryset(self):
        return Adaptacao.objects.visiveis_para(self.request.user)


class MaterialListaView(PaginaEmConstrucao):
    papeis = TODOS
    titulo = "Materiais"
    subtitulo = "Materiais enviados e suas adaptações."
    entrega = 8


class MaterialDetalheView(MateriaisVisiveisMixin, PaginaEmConstrucao):
    papeis = TODOS
    subtitulo = "O material e todas as adaptações feitas a partir dele."
    entrega = 8
    voltar = "materiais:lista"


class AdaptarView(PaginaEmConstrucao):
    papeis = PROFESSOR
    titulo = "Adaptar material"
    subtitulo = "1. Material (PDF)  2. Aluno  3. Formato. Aceita ?aluno=<id> e ?material=<id>."
    entrega = 7


class AdaptacaoDetalheView(AdaptacoesVisiveisMixin, PaginaEmConstrucao):
    """A tela "Material pronto": conteúdo, Ouvir, Refazer e Exportar."""

    papeis = TODOS
    subtitulo = "Material pronto: Ouvir, Refazer e Exportar."
    entrega = 8
    voltar = "materiais:lista"


class AdaptacaoRefazerView(AcaoEmConstrucao):
    papeis = PROFESSOR
    mensagem = "Refazer adaptação"
    entrega = 8
    destino = "materiais:adaptacao"
    destino_com_pk = True

    def get_queryset(self):
        # Só quem criou a adaptação pode refazê-la.
        return Adaptacao.objects.filter(criado_por=self.request.user)


class AdaptacaoExportarView(AdaptacoesVisiveisMixin, PaginaEmConstrucao):
    papeis = TODOS
    subtitulo = "Página pronta para imprimir ou salvar em PDF."
    entrega = 8

    def get_titulo(self, objeto):
        return f"Exportar: {objeto.material}"

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto["voltar_url"] = reverse("materiais:adaptacao", kwargs={"pk": self.kwargs["pk"]})
        return contexto
