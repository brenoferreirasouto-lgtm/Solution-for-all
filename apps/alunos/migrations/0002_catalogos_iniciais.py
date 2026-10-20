"""Preenche os catálogos de necessidades e formatos. Dá para editar depois pelo /admin/."""

from django.db import migrations

NECESSIDADES = [
    ("TEA", "tea"),
    ("TDAH", "tdah"),
    ("Dislexia", "dislexia"),
    ("Deficiência visual", "deficiencia-visual"),
    ("Deficiência auditiva", "deficiencia-auditiva"),
    ("Deficiência motora", "deficiencia-motora"),
]

FORMATOS = [
    (
        "Simples",
        "simples",
        "Texto simplificado, frases curtas.",
        "Reescreva o texto em linguagem simples, com frases curtas e palavras do dia a dia.",
    ),
    (
        "Resumo",
        "resumo",
        "Só as ideias principais.",
        "Resuma o texto nas ideias principais, em tópicos curtos.",
    ),
    (
        "Visual",
        "visual",
        "Esquema ou mapa mental.",
        "Organize o conteúdo como um esquema visual ou mapa mental, em passos numerados.",
    ),
    (
        "Áudio",
        "audio",
        "Texto pensado para ser ouvido.",
        "Reescreva o texto para ser lido em voz alta, sem tabelas nem símbolos.",
    ),
]


def criar_catalogos(apps, schema_editor):
    Necessidade = apps.get_model("alunos", "Necessidade")
    TipoAdaptacao = apps.get_model("alunos", "TipoAdaptacao")
    for ordem, (nome, slug) in enumerate(NECESSIDADES):
        Necessidade.objects.get_or_create(slug=slug, defaults={"nome": nome, "ordem": ordem})
    for ordem, (nome, slug, descricao, instrucao) in enumerate(FORMATOS):
        TipoAdaptacao.objects.get_or_create(
            slug=slug,
            defaults={"nome": nome, "descricao": descricao, "instrucao_ia": instrucao, "ordem": ordem},
        )


def remover_catalogos(apps, schema_editor):
    apps.get_model("alunos", "Necessidade").objects.filter(slug__in=[s for _, s in NECESSIDADES]).delete()
    apps.get_model("alunos", "TipoAdaptacao").objects.filter(slug__in=[f[1] for f in FORMATOS]).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("alunos", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(criar_catalogos, remover_catalogos),
    ]
