"""
Entregas do cronograma (16/10 a 05/12/2026).

As páginas "em construção" mostram qual entrega vai construir cada tela.
Quando uma entrega mudar de título, atualize aqui.
"""

ENTREGAS = {
    1: "Estrutura base do app web (layout, rotas, banco de dados)",
    2: "IA simulada no app + API gratuita escolhida e testada à parte",
    3: "Cadastro que diferencia professor e coordenador",
    4: "Coordenador cadastra professor e membro do núcleo psicopedagógico",
    5: "Coordenador cadastra alunos e perfil cognitivo",
    6: "Coordenador cadastra horários das aulas e alunos que precisam de atenção",
    7: "Menu de adaptação com IA (anexar arquivo, escolher aluno e tipo)",
    8: "Aba do conteúdo adaptado com botão de exportar",
    9: "Menu de introdução do professor (dados iniciais, adaptação rápida, alertas)",
    10: "Menu das \"três listras\" com lista de alunos e lupa de busca",
    11: "Aplicação da LGPD (consentimento e proteção dos dados)",
    12: "Menu de introdução do coordenador (dados iniciais e atalhos)",
    13: "Autenticador por código enviado ao e-mail (recuperar senha)",
    14: "Testes gerais, correção de bugs e ensaio da apresentação",
}


def entrega(numero):
    """Devolve {"numero": 5, "titulo": "..."} ou None."""
    if numero is None:
        return None
    return {"numero": numero, "titulo": ENTREGAS[numero]}
