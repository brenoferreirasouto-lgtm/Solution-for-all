from django.conf import settings
from django.db import models

from apps.contas.models import Papel
from apps.core.models import ModeloBase
from apps.escola.models import Turma


class Necessidade(ModeloBase):
    """Catálogo: TEA, TDAH, Dislexia, deficiência visual... Editável no /admin/."""

    nome = models.CharField("nome", max_length=80, unique=True)
    slug = models.SlugField("slug", unique=True, help_text="Usado nos filtros: /alunos/?necessidade=tea")
    ordem = models.PositiveSmallIntegerField("ordem", default=0)

    class Meta:
        verbose_name = "necessidade"
        verbose_name_plural = "necessidades"
        ordering = ["ordem", "nome"]

    def __str__(self):
        return self.nome


class TipoAdaptacao(ModeloBase):
    """Catálogo de formatos: Simples, Resumo, Visual, Áudio. Serve ao cadastro e à tela Adaptar."""

    nome = models.CharField("nome", max_length=80, unique=True)
    slug = models.SlugField("slug", unique=True)
    descricao = models.CharField("descrição", max_length=200, blank=True)
    instrucao_ia = models.TextField(
        "instrução para a IA",
        blank=True,
        help_text="Texto que o serviço de IA usa para pedir este formato.",
    )
    ordem = models.PositiveSmallIntegerField("ordem", default=0)

    class Meta:
        verbose_name = "tipo de adaptação"
        verbose_name_plural = "tipos de adaptação"
        ordering = ["ordem", "nome"]

    def __str__(self):
        return self.nome


class AlunoQuerySet(models.QuerySet):
    def ativos(self):
        return self.filter(ativo=True)

    def visiveis_para(self, usuario):
        """Coordenação e núcleo veem todos; o professor só vê os alunos vinculados a ele."""
        if not usuario.is_authenticated:
            return self.none()
        if usuario.papel in (Papel.COORDENADOR, Papel.NUCLEO):
            return self.all()
        return self.filter(professores=usuario).distinct()


class Aluno(ModeloBase):
    nome = models.CharField("nome", max_length=150)
    turma = models.ForeignKey(Turma, verbose_name="turma", on_delete=models.PROTECT, related_name="alunos")
    necessidades = models.ManyToManyField(
        Necessidade, verbose_name="necessidades", related_name="alunos", blank=True
    )
    formatos = models.ManyToManyField(
        TipoAdaptacao,
        verbose_name="formatos recomendados",
        related_name="alunos",
        blank=True,
        help_text="Já vêm selecionados na tela Adaptar material.",
    )
    professores = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        verbose_name="professores que acompanham",
        related_name="alunos_acompanhados",
        blank=True,
        limit_choices_to={"papel": Papel.PROFESSOR},
    )
    observacoes = models.TextField("observações", blank=True)
    plano_ia = models.BooleanField(
        "plano com IA",
        default=False,
        help_text="O que o plano gera ainda será definido (antes da entrega #5).",
    )
    precisa_atencao = models.BooleanField("precisa de atenção", default=False)
    motivo_atencao = models.CharField("motivo da atenção", max_length=200, blank=True)
    ativo = models.BooleanField("ativo", default=True, help_text="Arquivar = desmarcar. O histórico é mantido.")
    criado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="cadastrado por",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )

    objects = AlunoQuerySet.as_manager()

    class Meta:
        verbose_name = "aluno"
        verbose_name_plural = "alunos"
        ordering = ["nome"]

    def __str__(self):
        return self.nome

    @property
    def iniciais(self):
        partes = [p for p in self.nome.split() if p]
        if not partes:
            return ""
        if len(partes) == 1:
            return partes[0][:2].upper()
        return (partes[0][0] + partes[-1][0]).upper()
