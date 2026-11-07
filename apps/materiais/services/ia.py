"""
Serviço de IA do Solution for All.

Hoje a adaptação é SIMULADA: devolve um texto de exemplo, sem chamar
nenhuma API. A API gratuita é escolhida e testada à parte (entrega #2);
quando o grupo decidir ligá-la no app, só esta função muda. Views, banco e
rotas continuam iguais.

Regra de privacidade (LGPD): `gerar_adaptacao` recebe só o texto do material
e o formato; `gerar_plano_apoio` recebe só os itens de catálogo marcados no
cadastro (necessidades e formatos). Nunca passe o nome do aluno, as
observações nem dados de diagnóstico para a IA.
"""

from dataclasses import dataclass

LIMITE_TRECHO = 600


@dataclass(frozen=True)
class ResultadoIA:
    conteudo: str
    gerado_por: str


def gerar_adaptacao(texto: str, tipo) -> ResultadoIA:
    """
    Adapta `texto` para o formato `tipo` (um TipoAdaptacao).

    Versão simulada: monta um texto de exemplo com o começo do material.
    """
    trecho = " ".join((texto or "").split())[:LIMITE_TRECHO]
    if not trecho:
        trecho = "(o material enviado não tem texto legível)"
    conteudo = (
        f"[Adaptação simulada · formato {tipo.nome}]\n\n"
        f"{trecho}\n\n"
        "Este texto é um exemplo. A adaptação real chega quando a API de IA for ligada."
    )
    return ResultadoIA(conteudo=conteudo, gerado_por="simulada")


# Plano com IA do cadastro de aluno (entrega #5) ------------------------------
# Versão simulada: estratégias gerais por necessidade do catálogo. A IA de
# verdade receberia os mesmos dados (nomes do catálogo), nunca o aluno.
ESTRATEGIAS_POR_NECESSIDADE = {
    "tea": (
        "Antecipe a rotina da aula e avise com antecedência quando algo mudar.",
        "Dê uma instrução por vez, de forma direta, com apoio visual.",
        "Combine um sinal ou um espaço para pausa quando houver sobrecarga.",
    ),
    "tdah": (
        "Divida as atividades em etapas curtas, com pausas planejadas.",
        "Mostre o objetivo da tarefa no início e confira o andamento em pontos combinados.",
        "Reduza as distrações por perto e alterne tarefas paradas com tarefas com movimento.",
    ),
    "dislexia": (
        "Use fonte maior, espaçamento amplo e parágrafos curtos.",
        "Ofereça o conteúdo também em áudio e leia os enunciados em voz alta.",
        "Avalie a compreensão também de forma oral, sem penalizar a ortografia.",
    ),
    "deficiencia-visual": (
        "Prefira alto contraste e descreva imagens, gráficos e esquemas.",
        "Entregue arquivos que funcionem com leitor de tela e ampliação.",
    ),
    "deficiencia-auditiva": (
        "Acompanhe as explicações orais com texto escrito ou legenda.",
        "Fale de frente para a turma e use apoio visual nas instruções.",
    ),
    "deficiencia-motora": (
        "Dê mais tempo para atividades escritas e aceite resposta oral ou digital.",
        "Organize o material para exigir pouca manipulação.",
    ),
}


def gerar_plano_apoio(necessidades, formatos) -> ResultadoIA:
    """
    Sugere estratégias de apoio para o "Plano com IA" do cadastro de aluno.

    Recebe só itens de catálogo (Necessidade e TipoAdaptacao), nunca o aluno.
    Versão simulada: junta estratégias gerais de cada necessidade marcada.
    """
    partes = ["Sugestões de apoio (IA simulada)"]
    for necessidade in necessidades:
        estrategias = ESTRATEGIAS_POR_NECESSIDADE.get(necessidade.slug) or (
            "Combine com o núcleo psicopedagógico as estratégias de apoio mais adequadas.",
        )
        partes.append("\n".join([necessidade.nome, *(f"• {e}" for e in estrategias)]))
    if formatos:
        linhas = [
            f"• {f.nome}: {f.descricao}" if f.descricao else f"• {f.nome}" for f in formatos
        ]
        partes.append("\n".join(["Formatos recomendados para os materiais", *linhas]))
    if len(partes) == 1:
        partes.append("Marque ao menos uma necessidade ou um formato para a IA sugerir estratégias.")
    partes.append("Revise estas sugestões com o núcleo psicopedagógico antes de usar.")
    return ResultadoIA(conteudo="\n\n".join(partes), gerado_por="simulada")
