from django.conf import settings
from django.db import models
from django.db.models import Q

from apps.alunos.models import Aluno, TipoAdaptacao
from apps.contas.models import Papel
from apps.core.models import ModeloBase
from apps.escola.models import Disciplina


def _gestao(usuario):
    return usuario.papel in (Papel.COORDENADOR, Papel.NUCLEO)


class MaterialQuerySet(models.QuerySet):
    def visiveis_para(self, usuario):
        if not usuario.is_authenticated:
            return self.none()
        if _gestao(usuario):
            return self.all()
        return self.filter(professor=usuario)


class Material(ModeloBase):
    """O arquivo original que o professor envia (ex.: aula.pdf)."""

    titulo = models.CharField("título", max_length=200)
    arquivo = models.FileField("arquivo", upload_to="materiais/%Y/%m/")
    texto_extraido = models.TextField("texto extraído", blank=True)
    professor = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name="professor", on_delete=models.PROTECT, related_name="materiais"
    )
    disciplina = models.ForeignKey(
        Disciplina,
        verbose_name="disciplina",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="materiais",
    )

    objects = MaterialQuerySet.as_manager()

    class Meta:
        verbose_name = "material"
        verbose_name_plural = "materiais"
        ordering = ["-criado_em"]

    def __str__(self):
        return self.titulo


class AdaptacaoQuerySet(models.QuerySet):
    def visiveis_para(self, usuario):
        """Coordenação e núcleo veem todas; o professor vê as que criou e as dos alunos dele."""
        if not usuario.is_authenticated:
            return self.none()
        if _gestao(usuario):
            return self.all()
        return self.filter(Q(criado_por=usuario) | Q(aluno__professores=usuario)).distinct()


class Adaptacao(ModeloBase):
    """
    Cada geração da IA (inclusive cada "Refazer") vira uma linha.
    Juntas, elas formam o histórico do aluno.
    """

    class Status(models.TextChoices):
        PENDENTE = "PENDENTE", "Pendente"
        CONCLUIDA = "CONCLUIDA", "Concluída"
        ERRO = "ERRO", "Erro"

    material = models.ForeignKey(
        Material, verbose_name="material", on_delete=models.PROTECT, related_name="adaptacoes"
    )
    aluno = models.ForeignKey(Aluno, verbose_name="aluno", on_delete=models.PROTECT, related_name="adaptacoes")
    tipo = models.ForeignKey(
        TipoAdaptacao, verbose_name="formato", on_delete=models.PROTECT, related_name="adaptacoes"
    )
    conteudo = models.TextField("conteúdo gerado", blank=True)
    versao = models.PositiveSmallIntegerField("versão", default=1, help_text="Cada Refazer soma 1.")
    status = models.CharField("status", max_length=10, choices=Status.choices, default=Status.PENDENTE)
    gerado_por = models.CharField(
        "gerado por", max_length=80, default="simulada", help_text='"simulada" ou o nome do modelo de IA.'
    )
    foi_util = models.BooleanField("foi útil?", null=True, blank=True)
    criado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="criado por",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="adaptacoes_criadas",
    )

    objects = AdaptacaoQuerySet.as_manager()

    class Meta:
        verbose_name = "adaptação"
        verbose_name_plural = "adaptações"
        ordering = ["-criado_em"]

    def __str__(self):
        return f"{self.material} · {self.tipo} · {self.aluno} (v{self.versao})"
