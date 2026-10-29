"""
Equipe (coordenadores, professores e membros do núcleo) e horários das aulas.
Tudo aqui é da coordenação. A equipe é a entrega #3/#4; os horários, a #6
(ainda páginas "em construção").
"""

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import FormView, TemplateView

from apps.contas.models import Papel
from apps.core.permissoes import COORDENACAO, PapelRequeridoMixin
from apps.core.views import AcaoEmConstrucao, PaginaEmConstrucao

from .forms import FORMULARIO_POR_PAPEL, CoordenadorForm, NucleoForm, ProfessorForm
from .models import HorarioAula

Usuario = get_user_model()

SECOES_DA_EQUIPE = (
    (Papel.COORDENADOR, "Coordenação", "escola:coordenador_novo", "Novo coordenador"),
    (Papel.PROFESSOR, "Professores", "escola:professor_novo", "Novo professor"),
    (Papel.NUCLEO, "Núcleo psicopedagógico", "escola:nucleo_novo", "Novo membro do núcleo"),
)


class EquipeView(PapelRequeridoMixin, TemplateView):
    papeis = COORDENACAO
    template_name = "escola/equipe.html"

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        pessoas = Usuario.objects.order_by("nome")
        contexto["titulo"] = "Equipe"
        contexto["secoes"] = [
            {
                "titulo": titulo,
                "rota_novo": rota,
                "rotulo_novo": rotulo,
                "pessoas": [p for p in pessoas if p.papel == papel],
            }
            for papel, titulo, rota, rotulo in SECOES_DA_EQUIPE
        ]
        return contexto


class MembroFormMixin(PapelRequeridoMixin):
    papeis = COORDENACAO
    template_name = "escola/membro_form.html"
    success_url = reverse_lazy("escola:equipe")
    titulo = ""
    subtitulo = ""

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto.update(
            titulo=self.titulo,
            subtitulo=self.subtitulo,
            voltar_url=self.success_url,
            e_professor=isinstance(contexto["form"], ProfessorForm),
        )
        return contexto


class MembroNovoView(MembroFormMixin, FormView):
    """Cadastra uma pessoa nova. Cada subclasse fixa o papel, que não vem do formulário."""

    form_class = None
    mensagem = "Cadastro feito."

    def form_valid(self, form):
        usuario = form.save()
        messages.success(self.request, f"{usuario.nome} foi cadastrado(a). {self.mensagem}")
        return super().form_valid(form)


class CoordenadorNovoView(MembroNovoView):
    form_class = CoordenadorForm
    titulo = "Novo coordenador"
    subtitulo = "Acessa tudo: equipe, alunos, horários e catálogos."
    mensagem = "A pessoa já pode entrar como coordenação."


class ProfessorNovoView(MembroNovoView):
    form_class = ProfessorForm
    titulo = "Novo professor"
    subtitulo = "Nome, e-mail, turmas, matéria e alunos acompanhados."
    mensagem = "A pessoa já pode entrar como professor."


class NucleoNovoView(MembroNovoView):
    form_class = NucleoForm
    titulo = "Novo membro do núcleo"
    subtitulo = "Acompanha todos os alunos e cuida dos catálogos."
    mensagem = "A pessoa já pode entrar pelo núcleo psicopedagógico."


class MembroEditarView(MembroFormMixin, FormView):
    membro = None

    def get_membro(self):
        # O papel já foi conferido no dispatch, então quem não é coordenador
        # recebe 403 antes de qualquer busca (e não 404).
        if self.membro is None:
            self.membro = get_object_or_404(Usuario, pk=self.kwargs["pk"])
        return self.membro

    def get_form_class(self):
        return FORMULARIO_POR_PAPEL[self.get_membro().papel]

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["instance"] = self.get_membro()
        return kwargs

    def get_context_data(self, **kwargs):
        membro = self.get_membro()
        self.titulo = f"Editar {membro.nome}"
        self.subtitulo = membro.get_papel_display()
        return super().get_context_data(**kwargs)

    def form_valid(self, form):
        usuario = form.save()
        messages.success(self.request, f"Dados de {usuario.nome} atualizados.")
        return super().form_valid(form)


class MembroDesativarView(PapelRequeridoMixin, View):
    """Desativa o acesso (a pessoa não entra mais) ou reativa, se já estiver desativado."""

    papeis = COORDENACAO
    http_method_names = ["post"]

    def post(self, request, pk):
        membro = get_object_or_404(Usuario, pk=pk)
        if membro == request.user:
            messages.error(request, "Você não pode desativar o seu próprio acesso.")
        elif membro.is_active:
            membro.is_active = False
            membro.save(update_fields=["is_active"])
            messages.success(request, f"O acesso de {membro.nome} foi desativado.")
        else:
            membro.is_active = True
            membro.save(update_fields=["is_active"])
            messages.success(request, f"O acesso de {membro.nome} foi reativado.")
        return redirect("escola:equipe")


class HorariosMixin:
    def get_queryset(self):
        return HorarioAula.objects.all()


class HorariosView(PaginaEmConstrucao):
    papeis = COORDENACAO
    titulo = "Horários das aulas"
    subtitulo = "Grade semanal por turma. Alimenta o card \"Aulas de hoje\"."
    entrega = 6


class HorarioNovoView(PaginaEmConstrucao):
    papeis = COORDENACAO
    titulo = "Novo horário"
    entrega = 6
    voltar = "escola:horarios"


class HorarioEditarView(HorariosMixin, PaginaEmConstrucao):
    papeis = COORDENACAO
    entrega = 6
    voltar = "escola:horarios"

    def get_titulo(self, objeto):
        return f"Editar horário: {objeto}"


class HorarioExcluirView(HorariosMixin, AcaoEmConstrucao):
    papeis = COORDENACAO
    mensagem = "Excluir horário"
    entrega = 6
    destino = "escola:horarios"
