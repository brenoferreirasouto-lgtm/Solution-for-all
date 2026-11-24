"""
Busca de alunos (entrega #10), versão em Python básico.

Ignora maiúsculas e acentos ("joao" acha "João"). Cada palavra digitada
precisa aparecer no nome ou na turma do aluno, em qualquer ordem
("ana 7" acha "Ana Beatriz · 7º B").

Usa só: strings, listas, for, if e funções.
"""

TAMANHO_MAXIMO = 80

# Cada letra de COM_ACENTO é trocada pela letra que está na mesma posição em SEM_ACENTO.
COM_ACENTO = "áàâãäåéèêëíìîïóòôõöúùûüçñýÿ"
SEM_ACENTO = "aaaaaaeeeeiiiiooooouuuucnyy"


def normalizar(texto):
    """Minúsculas, sem acentos e com espaços simples."""
    if texto is None:
        texto = ""
    texto = texto.lower()
    resultado = ""
    for letra in texto:
        posicao = COM_ACENTO.find(letra)
        if posicao >= 0:
            resultado = resultado + SEM_ACENTO[posicao]
        else:
            resultado = resultado + letra
    # split() sem argumento junta espaços repetidos e tira os das pontas.
    return " ".join(resultado.split())


def limpar_termo(termo):
    """Tira espaços repetidos e limita o tamanho do que foi digitado na busca."""
    if termo is None:
        termo = ""
    return " ".join(termo.split())[:TAMANHO_MAXIMO]


def filtrar(alunos, termo):
    """Devolve a lista de alunos que combinam com o termo (todos, se o termo for vazio)."""
    palavras = normalizar(limpar_termo(termo)).split()
    if len(palavras) == 0:
        return list(alunos)

    encontrados = []
    for aluno in alunos:
        texto_do_aluno = normalizar(f"{aluno.nome} {aluno.turma.nome}")
        achou_todas = True
        for palavra in palavras:
            if palavra not in texto_do_aluno:
                achou_todas = False
        if achou_todas:
            encontrados.append(aluno)
    return encontrados
