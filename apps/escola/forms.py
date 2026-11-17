"""
Cadastro da equipe pela coordenação (entregas #3 e #4) e horários das aulas (#6).

Um formulário por papel: coordenador, professor e membro do núcleo. O papel
vem da tela escolhida, nunca de um campo que a pessoa possa trocar.
"""

from django import forms
from django.contrib.auth import get_user_model, password_validation
from django.db.models import Q

from apps.alunos.models import Aluno
from apps.contas.models import Papel

from .models import DiaSemana, Disciplina, HorarioAula, Lecionacao, Turma

Usuario = get_user_model()


class MembroForm(forms.ModelForm):
    """Nome, e-mail e senha inicial. Na edição, a senha só muda se for preenchida."""

    papel = None  # definido em cada subclasse

    senha1 = forms.CharField(
        label="Senha inicial",
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
        help_text="A pessoa entra com ela e pode trocá-la depois.",
    )
    senha2 = forms.CharField(
        label="Repita a senha",
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
    )

    class Meta:
        model = Usuario
        fields = ("nome", "email")
        widgets = {
            "nome": forms.TextInput(attrs={"autocomplete": "off"}),
            "email": forms.EmailInput(attrs={"autocomplete": "off", "placeholder": "pessoa@escola.com"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.edicao = self.instance.pk is not None
        if self.edicao:
            self.fields["senha1"].required = False
            self.fields["senha2"].required = False
            self.fields["senha1"].label = "Nova senha"
            self.fields["senha1"].help_text = "Deixe em branco para manter a senha atual."

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        repetidos = Usuario.objects.filter(email__iexact=email).exclude(pk=self.instance.pk)
        if repetidos.exists():
            raise forms.ValidationError("Já existe uma pessoa cadastrada com este e-mail.")
        return email

    def clean(self):
        dados = super().clean()
        senha1, senha2 = dados.get("senha1"), dados.get("senha2")
        if senha1 or senha2:
            if senha1 != senha2:
                self.add_error("senha2", "As senhas não são iguais.")
            elif senha1:
                candidato = Usuario(nome=dados.get("nome", ""), email=dados.get("email", ""))
                try:
                    password_validation.validate_password(senha1, candidato)
                except forms.ValidationError as erro:
                    self.add_error("senha1", erro)
        return dados

    def save(self, commit=True):
        usuario = super().save(commit=False)
        if not self.edicao:
            usuario.papel = self.papel
        if self.cleaned_data.get("senha1"):
            usuario.set_password(self.cleaned_data["senha1"])
        if commit:
            usuario.save()
            self.salvar_vinculos(usuario)
        return usuario

    def salvar_vinculos(self, usuario):
        """Ganchos para dados além do usuário (o professor tem turmas e alunos)."""


class CoordenadorForm(MembroForm):
    papel = Papel.COORDENADOR


class NucleoForm(MembroForm):
    papel = Papel.NUCLEO


class ProfessorForm(MembroForm):
    papel = Papel.PROFESSOR

    turmas = forms.ModelMultipleChoiceField(
        label="Turmas",
        queryset=Turma.objects.filter(ativo=True),
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )
    disciplina = forms.ModelChoiceField(
        label="Matéria",
        queryset=Disciplina.objects.all(),
        required=False,
        empty_label="Selecione",
        help_text="A matéria que o professor leciona nas turmas marcadas. Cadastre matérias novas em Catálogos.",
    )
    alunos = forms.ModelMultipleChoiceField(
        label="Alunos acompanhados",
        queryset=Aluno.objects.ativos(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        help_text="O professor só enxerga os alunos marcados aqui.",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.edicao:
            self.fields["alunos"].initial = self.instance.alunos_acompanhados.values_list("pk", flat=True)
            self.fields["turmas"].label = "Adicionar turmas"
            self.fields["turmas"].help_text = (
                "Marque para incluir novas turmas. Para remover uma, use Catálogos › Lecionações."
            )

    def clean(self):
        dados = super().clean()
        turmas, disciplina = dados.get("turmas"), dados.get("disciplina")
        if turmas and not disciplina:
            self.add_error("disciplina", "Escolha a matéria que o professor leciona nessas turmas.")
        elif disciplina and not turmas:
            self.add_error("turmas", "Marque ao menos uma turma para esta matéria.")
        return dados

    def salvar_vinculos(self, usuario):
        usuario.alunos_acompanhados.set(self.cleaned_data["alunos"])
        for turma in self.cleaned_data["turmas"]:
            Lecionacao.objects.get_or_create(
                professor=usuario, turma=turma, disciplina=self.cleaned_data["disciplina"]
            )


FORMULARIO_POR_PAPEL = {
    Papel.COORDENADOR: CoordenadorForm,
    Papel.PROFESSOR: ProfessorForm,
    Papel.NUCLEO: NucleoForm,
}


class HorarioForm(forms.ModelForm):
    """
    Uma aula na grade semanal (entrega #6).

    A tela pede turma, matéria e professor; a lecionação (quem ensina o quê
    em qual turma) é criada se ainda não existir. Não deixa a mesma turma nem
    o mesmo professor com duas aulas no mesmo horário.
    """

    turma = forms.ModelChoiceField(label="Turma", queryset=Turma.objects.none(), empty_label="Selecione")
    disciplina = forms.ModelChoiceField(
        label="Matéria",
        queryset=Disciplina.objects.all(),
        empty_label="Selecione",
        help_text="Cadastre matérias novas em Catálogos.",
    )
    professor = forms.ModelChoiceField(label="Professor", queryset=Usuario.objects.none(), empty_label="Selecione")

    field_order = ("turma", "disciplina", "professor", "dia_semana", "hora_inicio", "hora_fim")

    class Meta:
        model = HorarioAula
        fields = ("dia_semana", "hora_inicio", "hora_fim")
        labels = {"dia_semana": "Dia da semana", "hora_inicio": "Início", "hora_fim": "Fim"}
        widgets = {
            "hora_inicio": forms.TimeInput(attrs={"type": "time"}, format="%H:%M"),
            "hora_fim": forms.TimeInput(attrs={"type": "time"}, format="%H:%M"),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        turmas = Q(ativo=True)
        professores = Q(papel=Papel.PROFESSOR, is_active=True)
        if self.instance.pk:
            lecionacao = self.instance.lecionacao
            self.initial.update(
                turma=lecionacao.turma_id, disciplina=lecionacao.disciplina_id, professor=lecionacao.professor_id
            )
            # Mantém a turma e o professor atuais mesmo se tiverem sido desativados.
            turmas |= Q(pk=lecionacao.turma_id)
            professores |= Q(pk=lecionacao.professor_id)
        self.fields["turma"].queryset = Turma.objects.filter(turmas)
        self.fields["professor"].queryset = Usuario.objects.filter(professores).order_by("nome")
        self.fields["dia_semana"].choices = [("", "Selecione"), *DiaSemana.choices]

    def clean(self):
        dados = super().clean()
        inicio, fim = dados.get("hora_inicio"), dados.get("hora_fim")
        if inicio and fim and fim <= inicio:
            # Erro no campo: o Django então não repete o aviso da regra do banco.
            self.add_error("hora_fim", "O fim precisa ser depois do início.")
            return dados

        dia, turma, professor = dados.get("dia_semana"), dados.get("turma"), dados.get("professor")
        if dia is None or not (inicio and fim):
            return dados
        mesmo_horario = (
            HorarioAula.objects.filter(dia_semana=dia, hora_inicio__lt=fim, hora_fim__gt=inicio)
            .exclude(pk=self.instance.pk)
            .select_related("lecionacao__turma", "lecionacao__disciplina", "lecionacao__professor")
        )
        if turma:
            choque = mesmo_horario.filter(lecionacao__turma=turma).first()
            if choque:
                self.add_error(
                    None,
                    f"A turma {turma.nome} já tem {choque.lecionacao.disciplina} nesse horário "
                    f"({choque.hora_inicio:%H:%M} às {choque.hora_fim:%H:%M}).",
                )
        if professor:
            choque = mesmo_horario.filter(lecionacao__professor=professor).first()
            if choque:
                self.add_error(
                    None,
                    f"{professor.nome} já dá aula nesse horário: {choque.lecionacao.disciplina} na turma "
                    f"{choque.lecionacao.turma.nome} ({choque.hora_inicio:%H:%M} às {choque.hora_fim:%H:%M}).",
                )
        return dados

    def save(self, commit=True):
        horario = super().save(commit=False)
        horario.lecionacao, _ = Lecionacao.objects.get_or_create(
            professor=self.cleaned_data["professor"],
            turma=self.cleaned_data["turma"],
            disciplina=self.cleaned_data["disciplina"],
        )
        if commit:
            horario.save()
        return horario
