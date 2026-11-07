"""
Equipe (coordenadores, professores e membros do núcleo) e horários das aulas.
Tudo aqui é da coordenação. A equipe é a entrega #3/#4; os horários, a #6.
"""

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import CreateView, FormView, TemplateView, UpdateView

from apps.contas.models import Papel
from apps.core.permissoes import COORDENACAO, PapelRequeridoMixin

from .forms import FORMULARIO_POR_PAPEL, CoordenadorForm, HorarioForm, NucleoForm, ProfessorForm
from .models import DiaSemana, HorarioAula, Turma

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


# Horários das aulas (entrega #6) ---------------------------------------------


def url_da_grade(turma_id=None):
    url = reverse("escola:horarios")
    return f"{url}?turma={turma_id}" if turma_id else url


class HorariosView(PapelRequeridoMixin, TemplateView):
    """Grade semanal, um bloco por dia. ?turma=<id> mostra só uma turma."""

    papeis = COORDENACAO
    template_name = "escola/horarios.html"

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        turmas = Turma.objects.filter(ativo=True)
        turma = None
        turma_id = self.request.GET.get("turma", "")
        if turma_id.isdigit():
            turma = Turma.objects.filter(pk=turma_id).first()

        aulas = HorarioAula.objects.select_related(
            "lecionacao__turma", "lecionacao__disciplina", "lecionacao__professor"
        ).order_by("dia_semana", "hora_inicio", "lecionacao__turma__nome")
        if turma:
            aulas = aulas.filter(lecionacao__turma=turma)
        else:
            aulas = aulas.filter(lecionacao__turma__ativo=True)
        aulas = list(aulas)

        hoje = timezone.localdate().weekday()
        dias = []
        for numero, nome in DiaSemana.choices:
            do_dia = [a for a in aulas if a.dia_semana == numero]
            # Sábado só aparece quando tem aula.
            if numero == DiaSemana.SABADO and not do_dia:
                continue
            dias.append({"numero": numero, "nome": nome, "aulas": do_dia, "hoje": numero == hoje})

        contexto.update(
            titulo="Horários das aulas",
            subtitulo="Grade semanal por turma. Toque em uma aula para editar ou excluir.",
            turmas=turmas,
            turma=turma,
            dias=dias,
            total=len(aulas),
            url_novo=f"{reverse('escola:horario_novo')}?turma={turma.pk}" if turma else reverse("escola:horario_novo"),
        )
        return contexto


class HorarioFormMixin(PapelRequeridoMixin):
    papeis = COORDENACAO
    form_class = HorarioForm
    template_name = "escola/horario_form.html"

    def get_success_url(self):
        return url_da_grade(self.object.lecionacao.turma_id)

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        turma_id = None
        if self.object:
            turma_id = self.object.lecionacao.turma_id
        contexto.update(titulo=self.titulo, voltar_url=url_da_grade(turma_id))
        return contexto


class HorarioNovoView(HorarioFormMixin, CreateView):
    titulo = "Novo horário"

    def get_initial(self):
        inicial = super().get_initial()
        turma = self.request.GET.get("turma", "")
        if turma.isdigit():
            inicial["turma"] = int(turma)
        return inicial

    def form_valid(self, form):
        resposta = super().form_valid(form)
        messages.success(self.request, f"Horário cadastrado: {self.object}.")
        return resposta


class HorarioEditarView(HorarioFormMixin, UpdateView):
    titulo = "Editar horário"

    def get_queryset(self):
        return HorarioAula.objects.select_related("lecionacao__turma", "lecionacao__disciplina", "lecionacao__professor")

    def form_valid(self, form):
        resposta = super().form_valid(form)
        messages.success(self.request, f"Horário atualizado: {self.object}.")
        return resposta


class HorarioExcluirView(PapelRequeridoMixin, View):
    papeis = COORDENACAO
    http_method_names = ["post"]

    def post(self, request, pk):
        horario = get_object_or_404(HorarioAula.objects.select_related("lecionacao"), pk=pk)
        turma_id = horario.lecionacao.turma_id
        descricao = str(horario)
        horario.delete()
        messages.success(request, f"Horário excluído: {descricao}.")
        return redirect(url_da_grade(turma_id))
