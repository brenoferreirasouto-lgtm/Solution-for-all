from django.conf import settings
from django.db import models
from django.utils import timezone

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
    # Perfil cognitivo (entrega #5): o que a escola observa no dia a dia.
    # Nada de diagnóstico ou laudo aqui (Política de Privacidade, seção 3.2).
    como_aprende = models.TextField(
        "como aprende melhor",
        blank=True,
        help_text="Ex.: entende melhor com exemplos visuais e instruções curtas.",
    )
    dificuldades = models.TextField(
        "principais dificuldades",
        blank=True,
        help_text="Ex.: perde o foco em textos longos.",
    )
    estrategias = models.TextField(
        "estratégias que funcionam",
        blank=True,
        help_text="Ex.: dividir a tarefa em etapas e avisar antes de mudar de atividade.",
    )
    observacoes = models.TextField("observações", blank=True)

    plano_ia = models.BooleanField(
        "plano com IA",
        default=False,
        help_text="A IA sugere estratégias de apoio a partir das necessidades e dos formatos marcados.",
    )
    plano_ia_texto = models.TextField("sugestões da IA", blank=True)
    plano_ia_gerado_em = models.DateTimeField("sugestões geradas em", null=True, blank=True)

    # Alunos que precisam de atenção (entrega #6).
    precisa_atencao = models.BooleanField("precisa de atenção", default=False)
    motivo_atencao = models.CharField("motivo da atenção", max_length=200, blank=True)
    atencao_marcada_em = models.DateTimeField("atenção marcada em", null=True, blank=True)
    atencao_marcada_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="atenção marcada por",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )

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
    def tem_perfil(self):
        return any((self.como_aprende, self.dificuldades, self.estrategias, self.observacoes))

    def gerar_plano(self):
        """Preenche as sugestões do Plano com IA. Chame save() depois (o aluno já precisa ter pk)."""
        # Import aqui dentro: o serviço de IA mora em materiais, que depende de alunos.
        from apps.materiais.services.ia import gerar_plano_apoio

        # Só itens de catálogo vão para a IA: nunca o nome, o perfil escrito ou as observações.
        resultado = gerar_plano_apoio(list(self.necessidades.all()), list(self.formatos.all()))
        self.plano_ia_texto = resultado.conteudo
        self.plano_ia_gerado_em = timezone.now()

    def limpar_plano(self):
        self.plano_ia_texto = ""
        self.plano_ia_gerado_em = None

    def marcar_atencao(self, motivo, por):
        """Marca o aluno como "precisa de atenção" (ou troca o motivo). Chame save() depois."""
        if not self.precisa_atencao or self.motivo_atencao != motivo:
            self.atencao_marcada_em = timezone.now()
            self.atencao_marcada_por = por
        self.precisa_atencao = True
        self.motivo_atencao = motivo

    def desmarcar_atencao(self):
        self.precisa_atencao = False
        self.motivo_atencao = ""
        self.atencao_marcada_em = None
        self.atencao_marcada_por = None

    @property
    def iniciais(self):
        partes = [p for p in self.nome.split() if p]
        if not partes:
            return ""
        if len(partes) == 1:
            return partes[0][:2].upper()
        return (partes[0][0] + partes[-1][0]).upper()
