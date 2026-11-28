"""Gera uma adaptação (tela Adaptar e botão Refazer) e guarda no histórico do aluno."""

from django.db import transaction

from apps.escola.models import Lecionacao

from ..models import Adaptacao, Material, proxima_versao
from . import ia


def disciplina_do_professor(professor, turma):
    """A matéria que o professor dá na turma, quando é uma só (ex.: Ciências no 7º B)."""
    disciplinas = list(
        Lecionacao.objects.filter(professor=professor, turma=turma).values_list("disciplina", flat=True).distinct()
    )
    return disciplinas[0] if len(disciplinas) == 1 else None


@transaction.atomic
def criar_material(professor, titulo, texto, arquivo=None, turma=None):
    material = Material(
        titulo=titulo,
        texto_extraido=texto,
        professor=professor,
        disciplina_id=disciplina_do_professor(professor, turma) if turma else None,
    )
    if arquivo:
        material.arquivo = arquivo
    material.save()
    return material


def adaptar(material, aluno, tipo, usuario):
    """
    Pede a adaptação à IA e cria uma nova versão.

    Regra de privacidade: a IA recebe só o texto do material e o formato.
    O aluno entra apenas no registro, para o histórico dele.
    """
    adaptacao = Adaptacao(
        material=material,
        aluno=aluno,
        tipo=tipo,
        versao=proxima_versao(material, aluno, tipo),
        criado_por=usuario,
    )
    try:
        resultado = ia.gerar_adaptacao(material.texto_extraido, tipo)
    except ia.IAIndisponivel as erro:
        adaptacao.status = Adaptacao.Status.ERRO
        adaptacao.gerado_por = "groq" if ia.ia_real() else "simulada"
        adaptacao.mensagem_erro = erro.mensagem[:300]
    else:
        adaptacao.conteudo = resultado.conteudo
        adaptacao.gerado_por = resultado.gerado_por
        adaptacao.status = Adaptacao.Status.CONCLUIDA
    adaptacao.save()
    return adaptacao
