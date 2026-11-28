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
    """
    O conteúdo que o professor envia na tela Adaptar (entrega #7): um arquivo
    (PDF, Word ou .txt) ou um texto colado. O texto fica guardado para gerar
    outras adaptações sem enviar o arquivo de novo.
    """

    titulo = models.CharField("título", max_length=200)
    arquivo = models.FileField(
        "arquivo", upload_to="materiais/%Y/%m/", blank=True, help_text="Vazio quando o texto foi colado na tela."
    )
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

    @property
    def nome_arquivo(self):
        return self.arquivo.name.rsplit("/", 1)[-1] if self.arquivo else ""


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
    # Entrega #2: por que a IA não respondeu (limite gratuito, sem internet...). Aparece na tela.
    mensagem_erro = models.CharField("mensagem de erro", max_length=300, blank=True)
    foi_util = models.BooleanField("foi útil?", null=True, blank=True)
    # Entrega #8: o professor revisa o texto gerado antes de usar (Termos, seção 6).
    revisado_em = models.DateTimeField("revisado em", null=True, blank=True)
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

    @property
    def ia_simulada(self):
        return self.gerado_por == "simulada"

    @property
    def nome_da_ia(self):
        """Para as telas: "gpt-oss-120b (Groq)" ou "IA simulada"."""
        from .services.ia import nome_do_modelo

        return nome_do_modelo(self.gerado_por)

    @property
    def ia_leu_so_o_comeco(self):
        """A IA de verdade lê até um limite de caracteres; acima disso, o professor é avisado."""
        from .services.ia import material_cortado

        return (
            self.status == self.Status.CONCLUIDA
            and not self.ia_simulada
            and material_cortado(self.material.texto_extraido)
        )

    def proxima_versao(self):
        """Número da próxima versão deste material, para este aluno e formato."""
        return proxima_versao(self.material, self.aluno, self.tipo)


def proxima_versao(material, aluno, tipo):
    ultima = (
        Adaptacao.objects.filter(material=material, aluno=aluno, tipo=tipo)
        .aggregate(maior=models.Max("versao"))
        .get("maior")
    )
    return (ultima or 0) + 1
