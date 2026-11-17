"""Itens do menu (☰ no celular, barra lateral no desktop) conforme o papel."""

from django.urls import reverse

from apps.alunos.models import Aluno
from apps.contas.models import Papel

# (rótulo, rota, prefixos de rota que deixam o item marcado como atual)
INICIO = ("Início", "painel:painel", ("painel:",))
ALUNOS = ("Alunos", "alunos:lista", ("alunos:",))
MEUS_ALUNOS = ("Meus alunos", "alunos:lista", ("alunos:",))
ADAPTAR = ("Adaptar material", "materiais:adaptar", ("materiais:adaptar",))
MATERIAIS = ("Materiais", "materiais:lista", ("materiais:lista", "materiais:detalhe", "materiais:adaptacao"))
EQUIPE = ("Equipe", "escola:equipe", ("escola:equipe", "escola:coordenador_", "escola:professor_", "escola:nucleo_", "escola:membro_"))
HORARIOS = ("Horários", "escola:horarios", ("escola:horario",))

MENU_POR_PAPEL = {
    Papel.PROFESSOR: [INICIO, MEUS_ALUNOS, ADAPTAR, MATERIAIS],
    Papel.NUCLEO: [INICIO, ALUNOS, MATERIAIS],
    Papel.COORDENADOR: [INICIO, ALUNOS, EQUIPE, HORARIOS, MATERIAIS],
}


# Quantos alunos o menu carrega. Passou disso, a pessoa usa a busca (que consulta o banco todo).
LIMITE_ALUNOS_NO_MENU = 150


def alunos_do_menu(usuario):
    """Alunos ativos que o usuário pode ver (o professor só vê os dele), em ordem alfabética."""
    alunos = list(
        Aluno.objects.visiveis_para(usuario)
        .ativos()
        .select_related("turma")
        .only("id", "nome", "turma__nome")
        .order_by("nome")[: LIMITE_ALUNOS_NO_MENU + 1]
    )
    return alunos[:LIMITE_ALUNOS_NO_MENU], len(alunos) > LIMITE_ALUNOS_NO_MENU


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
    alunos, tem_mais = alunos_do_menu(usuario)
    return {
        "menu_itens": itens,
        "mostrar_catalogos": usuario.is_staff,
        "menu_alunos": alunos,
        "menu_alunos_tem_mais": tem_mais,
        "menu_alunos_titulo": "Meus alunos" if usuario.papel == Papel.PROFESSOR else "Alunos",
    }
