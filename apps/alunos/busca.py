"""
Busca de alunos (entrega #10).

Ignora maiúsculas e acentos ("joao" acha "João"), porque o SQLite só trata
assim as letras sem acento. Cada palavra digitada precisa aparecer no nome ou
na turma do aluno, em qualquer ordem ("ana 7" acha "Ana Beatriz · 7º B").
"""

import unicodedata

TAMANHO_MAXIMO = 80


def normalizar(texto):
    """Minúsculas, sem acentos e com espaços simples."""
    decomposto = unicodedata.normalize("NFD", texto or "")
    sem_acento = "".join(c for c in decomposto if not unicodedata.combining(c))
    return " ".join(sem_acento.casefold().split())


def limpar_termo(termo):
    return " ".join((termo or "").split())[:TAMANHO_MAXIMO]


def filtrar(alunos, termo):
    """Devolve a lista de alunos que combinam com o termo (todos, se o termo for vazio)."""
    palavras = normalizar(limpar_termo(termo)).split()
    if not palavras:
        return list(alunos)
    return [a for a in alunos if all(p in normalizar(f"{a.nome} {a.turma.nome}") for p in palavras)]
