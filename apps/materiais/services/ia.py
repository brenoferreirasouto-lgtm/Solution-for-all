"""
Serviço de IA do Solution for All.

Hoje a adaptação é SIMULADA: devolve um texto de exemplo, sem chamar
nenhuma API. A API gratuita é escolhida e testada à parte (entrega #2);
quando o grupo decidir ligá-la no app, só esta função muda. Views, banco e
rotas continuam iguais.

Regra de privacidade (LGPD): esta função recebe só o texto do material e o
formato. Nunca passe o nome do aluno nem dados de diagnóstico para a IA.
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
