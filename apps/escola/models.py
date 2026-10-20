from django.conf import settings
from django.db import models
from django.db.models import F, Q

from apps.contas.models import Papel
from apps.core.models import ModeloBase


class Turma(ModeloBase):
    nome = models.CharField("nome", max_length=50, help_text="Ex.: 7º B")
    ano_letivo = models.PositiveSmallIntegerField("ano letivo")
    ativo = models.BooleanField("ativa", default=True)

    class Meta:
        verbose_name = "turma"
        verbose_name_plural = "turmas"
        ordering = ["-ano_letivo", "nome"]
        constraints = [
            models.UniqueConstraint(fields=["nome", "ano_letivo"], name="turma_unica_por_ano"),
        ]

    def __str__(self):
        return f"{self.nome} ({self.ano_letivo})"


class Disciplina(ModeloBase):
    """A "Matéria" do protótipo."""

    nome = models.CharField("nome", max_length=80, unique=True, help_text="Ex.: Ciências")

    class Meta:
        verbose_name = "disciplina"
        verbose_name_plural = "disciplinas"
        ordering = ["nome"]

    def __str__(self):
        return self.nome


class Lecionacao(ModeloBase):
    """Quem ensina qual disciplina em qual turma (ex.: Prof. Francisco, Ciências, 7º B)."""

    professor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="professor",
        on_delete=models.PROTECT,
        related_name="lecionacoes",
        limit_choices_to={"papel": Papel.PROFESSOR},
    )
    turma = models.ForeignKey(Turma, verbose_name="turma", on_delete=models.PROTECT, related_name="lecionacoes")
    disciplina = models.ForeignKey(
        Disciplina, verbose_name="disciplina", on_delete=models.PROTECT, related_name="lecionacoes"
    )

    class Meta:
        verbose_name = "lecionação"
        verbose_name_plural = "lecionações"
        ordering = ["turma", "disciplina"]
        constraints = [
            models.UniqueConstraint(fields=["professor", "turma", "disciplina"], name="lecionacao_unica"),
        ]

    def __str__(self):
        return f"{self.disciplina} · {self.turma.nome} · {self.professor}"


class DiaSemana(models.IntegerChoices):
    # Mesma numeração do date.weekday() do Python (segunda = 0).
    SEGUNDA = 0, "Segunda"
    TERCA = 1, "Terça"
    QUARTA = 2, "Quarta"
    QUINTA = 3, "Quinta"
    SEXTA = 4, "Sexta"
    SABADO = 5, "Sábado"


class HorarioAula(ModeloBase):
    """Grade semanal. O card "Aulas de hoje" filtra pelo dia da semana."""

    lecionacao = models.ForeignKey(
        Lecionacao, verbose_name="aula", on_delete=models.CASCADE, related_name="horarios"
    )
    dia_semana = models.PositiveSmallIntegerField("dia da semana", choices=DiaSemana.choices)
    hora_inicio = models.TimeField("início")
    hora_fim = models.TimeField("fim")

    class Meta:
        verbose_name = "horário de aula"
        verbose_name_plural = "horários de aula"
        ordering = ["dia_semana", "hora_inicio"]
        constraints = [
            models.CheckConstraint(condition=Q(hora_fim__gt=F("hora_inicio")), name="horario_fim_depois_do_inicio"),
        ]

    def __str__(self):
        return f"{self.get_dia_semana_display()} {self.hora_inicio:%H:%M} · {self.lecionacao}"
