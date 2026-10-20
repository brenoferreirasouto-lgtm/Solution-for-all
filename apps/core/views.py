"""
Views genéricas do esqueleto.

Na entrega 1, cada rota mostra uma página "em construção" com o título da
tela, quem pode acessá-la e qual entrega vai construí-la. Quem pegar uma
entrega troca a view genérica pela view de verdade, mantendo a URL e o nome.
"""

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, resolve_url
from django.views import View
from django.views.generic import TemplateView

from apps.contas.models import Papel

from .entregas import entrega as dados_da_entrega
from .permissoes import PapelRequeridoMixin


class PaginaEmConstrucao(PapelRequeridoMixin, TemplateView):
    template_name = "core/em_construcao.html"
    titulo = ""
    subtitulo = ""
    entrega = None  # número da entrega no cronograma
    voltar = None  # nome da rota do botão ‹ no topo (ex.: "alunos:lista")

    def get_objeto(self):
        """Páginas de um registro (ex.: /alunos/3/) sobrescrevem get_queryset()."""
        if hasattr(self, "get_queryset"):
            return get_object_or_404(self.get_queryset(), pk=self.kwargs["pk"])
        return None

    def get_titulo(self, objeto):
        if self.titulo:
            return self.titulo
        return str(objeto) if objeto is not None else ""

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        objeto = self.get_objeto()
        contexto.update(
            objeto=objeto,
            titulo=self.get_titulo(objeto),
            subtitulo=self.subtitulo,
            entrega=dados_da_entrega(self.entrega),
            papeis_com_acesso=[Papel(p).label for p in self.papeis] if not self.publica else [],
            layout="layouts/auth.html" if self.publica else "layouts/app.html",
            voltar_url=resolve_url(self.voltar) if self.voltar else None,
        )
        return contexto


class AcaoEmConstrucao(PapelRequeridoMixin, View):
    """Ações que mudam dados (arquivar, desativar, refazer...). Só aceitam POST."""

    http_method_names = ["post"]
    mensagem = "Ação"
    entrega = None
    destino = "painel:painel"  # nome da rota; recebe pk quando `destino_com_pk = True`
    destino_com_pk = False

    def post(self, request, *args, **kwargs):
        if hasattr(self, "get_queryset"):
            get_object_or_404(self.get_queryset(), pk=self.kwargs["pk"])
        dados = dados_da_entrega(self.entrega)
        aviso = f"{self.mensagem}: em construção"
        if dados:
            aviso += f" (entrega #{dados['numero']})"
        messages.info(request, aviso + ".")
        if self.destino_com_pk:
            return redirect(self.destino, pk=self.kwargs["pk"])
        return redirect(self.destino)


class PrivacidadeView(PaginaEmConstrucao):
    publica = True
    titulo = "Privacidade e dados"
    subtitulo = "Como o Solution for All protege os dados dos estudantes."
    entrega = 11
