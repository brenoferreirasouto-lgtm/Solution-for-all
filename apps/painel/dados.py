"""
Dados dos painéis iniciais (entregas #9 e #12).

Cada função devolve um dicionário pronto para o template. Fica fora do
views.py para a view continuar curta e para dar para testar sem abrir a tela.
Só números e consultas: nenhuma função aqui escreve no banco.
"""

from django.db.models import Count, Q

from apps.alunos.models import Aluno, Necessidade
from apps.contas.models import Papel, Usuario
from apps.escola.models import HorarioAula
from apps.materiais.models import Adaptacao, Material

# Quantos alunos aparecem na "Adaptação rápida" do professor. Quem tem mais usa "Ver todos".
LIMITE_ADAPTACAO_RAPIDA = 6


def _aulas_de_hoje():
    """Aulas do dia da semana de hoje, já com tudo que o card mostra (sem consulta por aula)."""
    return HorarioAula.objects.de_hoje().select_related(
        "lecionacao__disciplina", "lecionacao__turma", "lecionacao__professor"
    )


def dados_professor(usuario):
    """Painel do professor: resumo, aulas de hoje, adaptação rápida e alunos que precisam de atenção."""
    # visiveis_para() já garante que o professor só enxerga os alunos vinculados a ele.
    alunos = Aluno.objects.visiveis_para(usuario).ativos()

    resumo = [
        {"rotulo": "Meus alunos", "valor": alunos.count(), "rota": "alunos:lista"},
        {
            "rotulo": "Adaptações feitas",
            "valor": Adaptacao.objects.filter(criado_por=usuario, status=Adaptacao.Status.CONCLUIDA).count(),
            "rota": "materiais:lista",
        },
        {"rotulo": "Materiais enviados", "valor": Material.objects.filter(professor=usuario).count(), "rota": "materiais:lista"},
    ]

    # Busca um a mais só para saber se existe o botão "Ver todos".
    rapidos = list(alunos.select_related("turma").order_by("nome")[: LIMITE_ADAPTACAO_RAPIDA + 1])

    return {
        "resumo": resumo,
        "aulas_hoje": _aulas_de_hoje().filter(lecionacao__professor=usuario),
        "alunos_rapidos": rapidos[:LIMITE_ADAPTACAO_RAPIDA],
        "tem_mais_alunos": len(rapidos) > LIMITE_ADAPTACAO_RAPIDA,
        "alunos_atencao": list(alunos.filter(precisa_atencao=True).select_related("turma").order_by("nome")),
    }


def dados_coordenacao():
    """Painel da coordenação: números da escola, aulas de hoje e alunos por necessidade."""
    usuarios = Usuario.objects.filter(is_active=True)
    alunos = Aluno.objects.ativos()

    resumo = [
        {"rotulo": "Professores", "valor": usuarios.filter(papel=Papel.PROFESSOR).count(), "rota": "escola:equipe"},
        {"rotulo": "Núcleo psicopedagógico", "valor": usuarios.filter(papel=Papel.NUCLEO).count(), "rota": "escola:equipe"},
        {"rotulo": "Alunos ativos", "valor": alunos.count(), "rota": "alunos:lista"},
        {"rotulo": "Precisam de atenção", "valor": alunos.filter(precisa_atencao=True).count(), "rota": "alunos:lista"},
    ]

    return {
        "resumo": resumo,
        "aulas_hoje": _aulas_de_hoje(),
        # Uma consulta só, com a contagem de alunos ativos de cada necessidade.
        "necessidades": Necessidade.objects.annotate(total=Count("alunos", filter=Q(alunos__ativo=True))),
    }
