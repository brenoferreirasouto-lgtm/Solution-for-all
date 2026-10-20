"""Itens do menu (☰ no celular, barra lateral no desktop) conforme o papel."""

from django.urls import reverse

from apps.contas.models import Papel

# (rótulo, rota, prefixos de rota que deixam o item marcado como atual)
INICIO = ("Início", "painel:painel", ("painel:",))
ALUNOS = ("Alunos", "alunos:lista", ("alunos:",))
MEUS_ALUNOS = ("Meus alunos", "alunos:lista", ("alunos:",))
ADAPTAR = ("Adaptar material", "materiais:adaptar", ("materiais:adaptar",))
MATERIAIS = ("Materiais", "materiais:lista", ("materiais:lista", "materiais:detalhe", "materiais:adaptacao"))
EQUIPE = ("Equipe", "escola:equipe", ("escola:equipe", "escola:professor_", "escola:nucleo_", "escola:membro_"))
HORARIOS = ("Horários", "escola:horarios", ("escola:horario",))

MENU_POR_PAPEL = {
    Papel.PROFESSOR: [INICIO, MEUS_ALUNOS, ADAPTAR, MATERIAIS],
    Papel.NUCLEO: [INICIO, ALUNOS, MATERIAIS],
    Papel.COORDENADOR: [INICIO, ALUNOS, EQUIPE, HORARIOS, MATERIAIS],
}


def menu(request):
    usuario = getattr(request, "user", None)
    if usuario is None or not usuario.is_authenticated:
        return {}

    atual = request.resolver_match.view_name if request.resolver_match else ""
    itens = []
    for rotulo, rota, prefixos in MENU_POR_PAPEL.get(usuario.papel, []):
        itens.append(
            {
                "rotulo": rotulo,
                "url": reverse(rota),
                "atual": any(atual.startswith(p) for p in prefixos),
            }
        )
    return {"menu_itens": itens, "mostrar_catalogos": usuario.is_staff}
