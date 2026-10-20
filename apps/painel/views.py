from django.shortcuts import redirect
from django.utils import timezone

from apps.contas.models import Papel
from apps.core.views import PaginaEmConstrucao


def inicio(request):
    """/ leva ao painel de quem está logado, ou ao login."""
    if request.user.is_authenticated:
        return redirect("painel:painel")
    return redirect("contas:entrar")


class PainelView(PaginaEmConstrucao):
    """Mesma URL para todos; o conteúdo muda pelo papel."""

    POR_PAPEL = {
        Papel.PROFESSOR: ("Painel do professor", "Resumo, adaptação rápida e alunos que precisam de atenção.", 9),
        Papel.COORDENADOR: ("Painel da coordenação", "Números da escola, aulas de hoje e atalhos.", 12),
        Papel.NUCLEO: ("Painel do núcleo", "Alunos acompanhados e adaptações recentes.", None),
    }

    def get_context_data(self, **kwargs):
        titulo, subtitulo, entrega = self.POR_PAPEL[self.request.user.papel]
        self.titulo, self.subtitulo, self.entrega = titulo, subtitulo, entrega
        contexto = super().get_context_data(**kwargs)
        hora = timezone.localtime().hour
        cumprimento = "Bom dia" if hora < 12 else "Boa tarde" if hora < 18 else "Boa noite"
        contexto["saudacao"] = f"{cumprimento}, {self.request.user.get_short_name()}"
        return contexto
