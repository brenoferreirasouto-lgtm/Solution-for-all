from django.shortcuts import redirect
from django.utils import timezone

from apps.contas.models import Papel
from apps.core.views import PaginaEmConstrucao

from .dados import dados_coordenacao, dados_professor


def inicio(request):
    """/ leva ao painel de quem está logado, ou ao login."""
    if request.user.is_authenticated:
        return redirect("painel:painel")
    return redirect("contas:entrar")


class PainelView(PaginaEmConstrucao):
    """Mesma URL para todos; o conteúdo muda pelo papel.

    Professor (#9) e coordenador (#12) já têm tela de verdade. O núcleo ainda
    não tem entrega no cronograma e continua na página "em construção".
    """

    POR_PAPEL = {
        Papel.PROFESSOR: ("Painel do professor", "Resumo, adaptação rápida e alunos que precisam de atenção.", None),
        Papel.COORDENADOR: ("Painel da coordenação", "Números da escola, aulas de hoje e atalhos.", None),
        Papel.NUCLEO: ("Painel do núcleo", "Alunos acompanhados e adaptações recentes.", None),
    }

    TEMPLATE_POR_PAPEL = {
        Papel.PROFESSOR: "painel/professor.html",
        Papel.COORDENADOR: "painel/coordenacao.html",
    }

    def get_template_names(self):
        return [self.TEMPLATE_POR_PAPEL.get(self.request.user.papel, self.template_name)]

    def get_context_data(self, **kwargs):
        usuario = self.request.user
        titulo, subtitulo, entrega = self.POR_PAPEL[usuario.papel]
        self.titulo, self.subtitulo, self.entrega = titulo, subtitulo, entrega
        contexto = super().get_context_data(**kwargs)
        hora = timezone.localtime().hour
        cumprimento = "Bom dia" if hora < 12 else "Boa tarde" if hora < 18 else "Boa noite"
        contexto["saudacao"] = f"{cumprimento}, {usuario.get_short_name()}"
        if usuario.papel == Papel.PROFESSOR:
            contexto.update(dados_professor(usuario))
        elif usuario.papel == Papel.COORDENADOR:
            contexto.update(dados_coordenacao())
        return contexto
