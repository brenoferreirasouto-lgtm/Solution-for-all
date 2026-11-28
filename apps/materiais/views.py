"""
Materiais e adaptações.

Entrega #7: tela Adaptar material (aluno, conteúdo e formato).
Entrega #8: material pronto (revisar e Salvar, Ouvir, Refazer, Exportar) e as
listas de materiais.

Professor vê os materiais que enviou e as adaptações dos alunos dele;
coordenação e núcleo veem tudo. Só o professor adapta, e só quem criou a
adaptação revisa e refaz.
"""

import io

from django.contrib import messages
from django.db.models import Count
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify
from django.views import View
from django.views.generic import DetailView, FormView, TemplateView

from apps.alunos.models import Aluno
from apps.contas.models import Papel
from apps.core.permissoes import PROFESSOR, TODOS, PapelRequeridoMixin

from .forms import AdaptarForm, RevisarForm
from .models import Adaptacao, Material
from .services.adaptacoes import adaptar, criar_material
from .services.ia import LIMITE_ENTRADA_IA, ia_real


class MateriaisVisiveisMixin:
    def get_queryset(self):
        return Material.objects.visiveis_para(self.request.user)


class AdaptacoesVisiveisMixin:
    def get_queryset(self):
        return Adaptacao.objects.visiveis_para(self.request.user).select_related(
            "material", "aluno__turma", "tipo", "criado_por"
        )


def blocos_do_texto(conteudo):
    """Parágrafos do texto adaptado (separados por linha em branco), cada um com suas linhas."""
    blocos = [b.strip() for b in (conteudo or "").replace("\r\n", "\n").split("\n\n")]
    return [b.split("\n") for b in blocos if b]


# Entrega #8: listas -----------------------------------------------------------
class MaterialListaView(PapelRequeridoMixin, TemplateView):
    papeis = TODOS
    template_name = "materiais/lista.html"

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        usuario = self.request.user
        professor = usuario.papel == Papel.PROFESSOR
        contexto.update(
            titulo="Materiais",
            subtitulo=(
                "Os materiais que você enviou. Toque em um para ver as adaptações."
                if professor
                else "Os materiais que os professores enviaram e as adaptações feitas com eles."
            ),
            materiais=(
                Material.objects.visiveis_para(usuario)
                .select_related("professor", "disciplina")
                .annotate(total_adaptacoes=Count("adaptacoes"))
                .order_by("-criado_em")
            ),
            pode_adaptar=professor,
            mostrar_professor=not professor,
        )
        return contexto


class MaterialDetalheView(MateriaisVisiveisMixin, PapelRequeridoMixin, DetailView):
    papeis = TODOS
    template_name = "materiais/detalhe.html"
    context_object_name = "material"

    def get_queryset(self):
        return super().get_queryset().select_related("professor", "disciplina")

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        usuario = self.request.user
        material = self.object
        contexto.update(
            titulo=material.titulo,
            voltar_url=reverse("materiais:lista"),
            adaptacoes=(
                Adaptacao.objects.visiveis_para(usuario)
                .filter(material=material)
                .select_related("aluno__turma", "tipo")
                .order_by("aluno__nome", "tipo__ordem", "-versao")
            ),
            pode_adaptar=usuario.papel == Papel.PROFESSOR and material.professor_id == usuario.pk,
        )
        return contexto


# Entrega #7: Adaptar material ---------------------------------------------------
class AdaptarView(PapelRequeridoMixin, FormView):
    """1. Aluno, 2. Conteúdo, 3. Formato. Aceita ?aluno=<id> e ?material=<id>."""

    papeis = PROFESSOR
    template_name = "materiais/adaptar.html"
    form_class = AdaptarForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["usuario"] = self.request.user
        return kwargs

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        if self.request.method == "GET":
            self.preencher(form)
        return form

    def preencher(self, form):
        """Usa ?aluno= e ?material= quando são do professor; o formato vem do perfil do aluno."""
        aluno_id = self.request.GET.get("aluno", "")
        if aluno_id.isdigit():
            aluno = form.fields["aluno"].queryset.filter(pk=aluno_id).first()
            if aluno:
                form.initial["aluno"] = aluno.pk
                formato = aluno.formatos.order_by("ordem").first()
                if formato:
                    form.initial["tipo"] = formato.pk
        material_id = self.request.GET.get("material", "")
        if material_id.isdigit() and form.fields["material"].queryset.filter(pk=material_id).exists():
            form.initial.update(origem=AdaptarForm.MATERIAL, material=int(material_id))

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto.update(
            titulo="Adaptar material",
            subtitulo="Escolha o aluno, envie o conteúdo e o formato. A IA recebe só o texto do material, nunca os dados do aluno.",
            sem_alunos=not contexto["form"].fields["aluno"].queryset.exists(),
            ia_real=ia_real(),
            limite_ia=f"{LIMITE_ENTRADA_IA:,}".replace(",", "."),
        )
        return contexto

    def form_valid(self, form):
        dados = form.cleaned_data
        usuario = self.request.user
        aluno = dados["aluno"]
        if dados["origem"] == AdaptarForm.MATERIAL:
            material = dados["material"]
        else:
            material = criar_material(
                professor=usuario,
                titulo=dados["titulo_final"],
                texto=dados["texto_final"],
                arquivo=dados.get("arquivo") if dados["origem"] == AdaptarForm.ARQUIVO else None,
                turma=aluno.turma,
            )
        adaptacao = adaptar(material, aluno, dados["tipo"], usuario)
        if adaptacao.status == Adaptacao.Status.ERRO:
            messages.error(self.request, "O material ficou salvo, mas a adaptação não foi gerada. Veja o motivo abaixo.")
        else:
            messages.success(self.request, f"Material adaptado para {aluno.nome}. Revise o texto antes de usar.")
        return redirect("materiais:adaptacao", pk=adaptacao.pk)


# Entrega #8: material pronto ------------------------------------------------------
class AdaptacaoDetalheView(AdaptacoesVisiveisMixin, PapelRequeridoMixin, DetailView):
    """A tela "Material adaptado": texto, Salvar (revisão), Ouvir, Refazer e Exportar."""

    papeis = TODOS
    template_name = "materiais/adaptacao.html"
    context_object_name = "adaptacao"

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        usuario = self.request.user
        adaptacao = self.object
        e_autor = usuario.papel == Papel.PROFESSOR and adaptacao.criado_por_id == usuario.pk
        material_visivel = Material.objects.visiveis_para(usuario).filter(pk=adaptacao.material_id).exists()
        # Altura inicial do campo de revisão: conta as quebras que o texto terá no celular.
        linhas = sum(max(1, -(-len(linha) // 40)) for linha in (adaptacao.conteudo or "").split("\n")) + 2
        contexto.update(
            titulo=adaptacao.material.titulo,
            voltar_url=(
                reverse("materiais:detalhe", kwargs={"pk": adaptacao.material_id})
                if material_visivel
                else reverse("materiais:lista")
            ),
            e_autor=e_autor,
            form=RevisarForm(initial={"conteudo": adaptacao.conteudo}) if e_autor else None,
            linhas=min(max(linhas, 8), 40),
            blocos=blocos_do_texto(adaptacao.conteudo),
            aluno_visivel=Aluno.objects.visiveis_para(usuario).filter(pk=adaptacao.aluno_id).exists(),
            material_visivel=material_visivel,
            outras_versoes=(
                Adaptacao.objects.visiveis_para(usuario)
                .filter(material=adaptacao.material_id, aluno=adaptacao.aluno_id, tipo=adaptacao.tipo_id)
                .exclude(pk=adaptacao.pk)
                .order_by("-versao")
            ),
        )
        return contexto


class AcaoDoAutorMixin(PapelRequeridoMixin):
    """Salvar e Refazer: só POST e só para o professor que criou a adaptação."""

    papeis = PROFESSOR
    http_method_names = ["post"]

    def get_queryset(self):
        return Adaptacao.objects.filter(criado_por=self.request.user).select_related("material", "aluno", "tipo")

    def get_adaptacao(self):
        return get_object_or_404(self.get_queryset(), pk=self.kwargs["pk"])


class AdaptacaoSalvarView(AcaoDoAutorMixin, View):
    """Salvar do protótipo: grava o texto revisado pelo professor."""

    def post(self, request, pk):
        adaptacao = self.get_adaptacao()
        form = RevisarForm(request.POST)
        if not form.is_valid():
            messages.error(request, " ".join(form.errors["conteudo"]))
            return redirect("materiais:adaptacao", pk=adaptacao.pk)
        adaptacao.conteudo = form.cleaned_data["conteudo"]
        adaptacao.revisado_em = timezone.now()
        adaptacao.save(update_fields=["conteudo", "revisado_em", "atualizado_em"])
        messages.success(request, "Texto revisado e salvo.")
        return redirect("materiais:adaptacao", pk=adaptacao.pk)


class AdaptacaoRefazerView(AcaoDoAutorMixin, View):
    """Gera uma nova versão. A anterior continua no histórico."""

    def post(self, request, pk):
        anterior = self.get_adaptacao()
        nova = adaptar(anterior.material, anterior.aluno, anterior.tipo, request.user)
        if nova.status == Adaptacao.Status.ERRO:
            messages.error(request, "A nova versão não foi gerada. Veja o motivo abaixo.")
        else:
            aviso = f"Versão {nova.versao} gerada. A versão {anterior.versao} continua no histórico."
            if nova.ia_simulada:
                aviso += " Com a IA simulada, o texto sai igual; com a IA de verdade, cada versão muda."
            messages.success(request, aviso)
        return redirect("materiais:adaptacao", pk=nova.pk)


class AdaptacaoExportarView(AdaptacoesVisiveisMixin, PapelRequeridoMixin, DetailView):
    """Página limpa para imprimir ou salvar em PDF. Não mostra o nome nem as necessidades do aluno."""

    papeis = TODOS
    template_name = "materiais/exportar.html"
    context_object_name = "adaptacao"

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto.update(
            titulo=f"Exportar: {self.object.material.titulo}",
            voltar_url=reverse("materiais:adaptacao", kwargs={"pk": self.object.pk}),
            blocos=blocos_do_texto(self.object.conteudo),
            nota=nota_de_origem(self.object),
        )
        return contexto


class AdaptacaoWordView(AdaptacoesVisiveisMixin, PapelRequeridoMixin, View):
    """Baixa o texto adaptado em Word (.docx), para o professor editar ou imprimir."""

    papeis = TODOS

    def get(self, request, pk):
        import docx
        from docx.shared import Pt

        adaptacao = get_object_or_404(self.get_queryset(), pk=pk)
        documento = docx.Document()
        documento.styles["Normal"].font.size = Pt(14)
        documento.add_heading(adaptacao.material.titulo, level=1)
        for linhas in blocos_do_texto(adaptacao.conteudo):
            paragrafo = documento.add_paragraph()
            for indice, linha in enumerate(linhas):
                if indice:
                    paragrafo.add_run().add_break()
                paragrafo.add_run(linha)
        rodape = documento.add_paragraph(nota_de_origem(adaptacao))
        rodape.runs[0].font.size = Pt(9)

        saida = io.BytesIO()
        documento.save(saida)
        nome = f"{slugify(adaptacao.material.titulo) or 'material'}-{adaptacao.tipo.slug}.docx"
        resposta = HttpResponse(
            saida.getvalue(),
            content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
        resposta["Content-Disposition"] = f'attachment; filename="{nome}"'
        return resposta


def nota_de_origem(adaptacao):
    """Rodapé do material exportado: diz que houve IA e se o professor revisou."""
    ia = "IA simulada" if adaptacao.ia_simulada else "IA"
    nota = f"Material adaptado com apoio de {ia} · formato {adaptacao.tipo.nome}"
    if adaptacao.revisado_em:
        nota += f" · revisado pelo professor em {timezone.localtime(adaptacao.revisado_em):%d/%m/%Y}"
    return nota + "."
