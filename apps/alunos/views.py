"""
Telas de alunos.

Entrega #5: cadastro, edição, perfil e arquivamento. Entrega #6: marcar quem
precisa de atenção. A busca e os filtros da lista ficam para a entrega #10.

Professor vê só os alunos vinculados a ele; coordenação e núcleo veem todos.
Cadastrar, editar, marcar atenção e gerar o plano com IA: coordenação e
núcleo. Arquivar: só a coordenação.
"""

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views import View
from django.views.generic import CreateView, DetailView, TemplateView, UpdateView

from apps.contas.models import Papel
from apps.core.permissoes import COORDENACAO, GESTAO, TODOS, PapelRequeridoMixin
from apps.materiais.models import Adaptacao

from .forms import AlunoForm, AtencaoForm
from .models import Aluno


class AlunosVisiveisMixin:
    def get_queryset(self):
        return Aluno.objects.visiveis_para(self.request.user)


class AlunoListaView(PapelRequeridoMixin, TemplateView):
    """Lista simples para chegar aos perfis. A lupa de busca e os filtros são da entrega #10."""

    papeis = TODOS
    template_name = "alunos/lista.html"

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        usuario = self.request.user
        gestao = usuario.papel in GESTAO
        alunos = list(
            Aluno.objects.visiveis_para(usuario)
            .select_related("turma")
            .prefetch_related("necessidades")
            .order_by("nome")
        )
        ativos = [a for a in alunos if a.ativo]
        contexto.update(
            titulo="Alunos" if gestao else "Meus alunos",
            subtitulo=(
                "Todos os alunos da escola. Toque em um nome para ver o perfil."
                if gestao
                else "Os alunos que você acompanha. Toque em um nome para ver o perfil."
            ),
            atencao=[a for a in ativos if a.precisa_atencao],
            ativos=ativos,
            arquivados=[a for a in alunos if not a.ativo] if gestao else [],
            pode_cadastrar=gestao,
        )
        return contexto


class AlunoFormMixin(PapelRequeridoMixin):
    papeis = GESTAO
    form_class = AlunoForm
    template_name = "alunos/form.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["usuario"] = self.request.user
        return kwargs

    def get_success_url(self):
        return reverse("alunos:detalhe", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto.update(
            titulo=self.titulo(),
            subtitulo="Dados, perfil cognitivo, professores e atenção.",
            voltar_url=self.voltar_url(),
            sem_turmas=not contexto["form"].fields["turma"].queryset.exists(),
        )
        return contexto


class AlunoNovoView(AlunoFormMixin, CreateView):
    def titulo(self):
        return "Novo aluno"

    def voltar_url(self):
        return reverse("alunos:lista")

    def form_valid(self, form):
        resposta = super().form_valid(form)
        messages.success(self.request, f"{self.object.nome} foi cadastrado(a).")
        return resposta


class AlunoEditarView(AlunosVisiveisMixin, AlunoFormMixin, UpdateView):
    def titulo(self):
        return f"Editar {self.object.nome}"

    def voltar_url(self):
        return reverse("alunos:detalhe", kwargs={"pk": self.object.pk})

    def form_valid(self, form):
        resposta = super().form_valid(form)
        messages.success(self.request, f"Perfil de {self.object.nome} atualizado.")
        return resposta


class AlunoDetalheView(AlunosVisiveisMixin, PapelRequeridoMixin, DetailView):
    papeis = TODOS
    template_name = "alunos/detalhe.html"
    context_object_name = "aluno"

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .select_related("turma", "criado_por", "atencao_marcada_por")
            .prefetch_related("necessidades", "formatos", "professores")
        )

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        usuario = self.request.user
        aluno = self.object
        contexto.update(
            titulo=aluno.nome,
            voltar_url=reverse("alunos:lista"),
            pode_editar=usuario.papel in GESTAO,
            pode_arquivar=usuario.papel in COORDENACAO,
            e_professor=usuario.papel == Papel.PROFESSOR,
            adaptacoes=(
                Adaptacao.objects.visiveis_para(usuario)
                .filter(aluno=aluno)
                .select_related("material", "tipo")
                .order_by("-criado_em")[:20]
            ),
        )
        return contexto


class AcaoDoAlunoMixin(AlunosVisiveisMixin, PapelRequeridoMixin):
    """Ações do perfil: só POST e sempre voltam para o perfil."""

    http_method_names = ["post"]

    def get_aluno(self):
        return get_object_or_404(self.get_queryset(), pk=self.kwargs["pk"])

    def voltar(self, aluno):
        return redirect("alunos:detalhe", pk=aluno.pk)


class AlunoArquivarView(AcaoDoAlunoMixin, View):
    """Arquiva (some das listas e das telas de adaptação) ou reativa. O histórico fica."""

    papeis = COORDENACAO

    def post(self, request, pk):
        aluno = self.get_aluno()
        aluno.ativo = not aluno.ativo
        aluno.save(update_fields=["ativo", "atualizado_em"])
        if aluno.ativo:
            messages.success(request, f"{aluno.nome} voltou para a lista de alunos.")
        else:
            messages.success(request, f"{aluno.nome} foi arquivado(a). O histórico continua guardado.")
        return self.voltar(aluno)


class AlunoAtencaoView(AcaoDoAlunoMixin, View):
    """Marca com motivo ou tira da lista de alunos que precisam de atenção."""

    papeis = GESTAO

    def post(self, request, pk):
        aluno = self.get_aluno()
        form = AtencaoForm(request.POST)
        if not form.is_valid():
            erros = [e for lista in form.errors.values() for e in lista]
            messages.error(request, " ".join(erros) or "Não foi possível salvar.")
            return self.voltar(aluno)
        if form.cleaned_data["acao"] == "marcar":
            aluno.marcar_atencao(form.cleaned_data["motivo"], request.user)
            messages.success(request, f"{aluno.nome} está na lista de quem precisa de atenção.")
        else:
            aluno.desmarcar_atencao()
            messages.success(request, f"{aluno.nome} saiu da lista de quem precisa de atenção.")
        aluno.save(
            update_fields=[
                "precisa_atencao",
                "motivo_atencao",
                "atencao_marcada_em",
                "atencao_marcada_por",
                "atualizado_em",
            ]
        )
        return self.voltar(aluno)


class AlunoPlanoView(AcaoDoAlunoMixin, View):
    """Gera de novo as sugestões do Plano com IA (com as necessidades e formatos atuais)."""

    papeis = GESTAO

    def post(self, request, pk):
        aluno = self.get_aluno()
        if not aluno.plano_ia:
            messages.info(request, "Ligue o Plano com IA em Editar para gerar sugestões.")
            return self.voltar(aluno)
        aluno.gerar_plano()
        aluno.save(update_fields=["plano_ia_texto", "plano_ia_gerado_em", "atualizado_em"])
        messages.success(request, "Sugestões da IA atualizadas.")
        return self.voltar(aluno)
