"""
Cadastro da equipe pela coordenação (entregas #3 e #4).

Um formulário por papel: coordenador, professor e membro do núcleo. O papel
vem da tela escolhida, nunca de um campo que a pessoa possa trocar.
"""

from django import forms
from django.contrib.auth import get_user_model, password_validation

from apps.alunos.models import Aluno
from apps.contas.models import Papel

from .models import Disciplina, Lecionacao, Turma

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
