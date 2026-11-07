"""
Cadastro de aluno e perfil cognitivo (entrega #5) e marcação de atenção (#6).

Coordenação e núcleo usam o mesmo formulário. Quem cadastrou, quando a
atenção foi marcada e as sugestões da IA são preenchidos aqui, nunca pela tela.
"""

from django import forms
from django.contrib.auth import get_user_model
from django.db.models import Q

from apps.contas.models import Papel
from apps.escola.models import Turma

from .models import Aluno

Usuario = get_user_model()

AVISO_PERFIL = "Descreva o que a escola observa no dia a dia. Não registre diagnósticos nem dados de laudos."


class AlunoForm(forms.ModelForm):
    class Meta:
        model = Aluno
        fields = (
            "nome",
            "turma",
            "necessidades",
            "formatos",
            "como_aprende",
            "dificuldades",
            "estrategias",
            "observacoes",
            "professores",
            "plano_ia",
            "precisa_atencao",
            "motivo_atencao",
        )
        labels = {
            "plano_ia": "Gerar sugestões de apoio com IA",
            "precisa_atencao": "Este aluno precisa de atenção",
        }
        help_texts = {
            "observacoes": AVISO_PERFIL,
            "professores": "O professor só enxerga os alunos marcados aqui.",
            "motivo_atencao": "Aparece para os professores do aluno. Ex.: voltou de afastamento e precisa retomar o conteúdo.",
        }
        widgets = {
            "nome": forms.TextInput(attrs={"autocomplete": "off"}),
            "necessidades": forms.CheckboxSelectMultiple,
            "formatos": forms.CheckboxSelectMultiple,
            "professores": forms.CheckboxSelectMultiple,
            "como_aprende": forms.Textarea(attrs={"rows": 3}),
            "dificuldades": forms.Textarea(attrs={"rows": 3}),
            "estrategias": forms.Textarea(attrs={"rows": 3}),
            "observacoes": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, usuario=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.usuario = usuario
        atual = self.instance if self.instance.pk else None
        # O ModelForm copia os dados da tela para o aluno ao validar; guardamos
        # o estado de antes para saber se a atenção foi marcada agora.
        self.atencao_antes = (self.instance.precisa_atencao, self.instance.motivo_atencao)

        # Turmas e professores ativos; na edição, mantém os que o aluno já tem.
        turmas = Q(ativo=True)
        professores = Q(papel=Papel.PROFESSOR, is_active=True)
        if atual:
            turmas |= Q(pk=atual.turma_id)
            professores |= Q(pk__in=atual.professores.values("pk"))
        self.fields["turma"].queryset = Turma.objects.filter(turmas)
        self.fields["turma"].empty_label = "Selecione"
        self.fields["professores"].queryset = Usuario.objects.filter(professores).order_by("nome")

        for nome in ("como_aprende", "dificuldades", "estrategias"):
            self.fields[nome].help_text = f"{self.fields[nome].help_text} {AVISO_PERFIL}".strip()

    def clean_nome(self):
        return " ".join(self.cleaned_data["nome"].split())

    def clean(self):
        dados = super().clean()
        motivo = (dados.get("motivo_atencao") or "").strip()
        dados["motivo_atencao"] = motivo
        if dados.get("precisa_atencao") and not motivo:
            self.add_error("motivo_atencao", "Diga o motivo, para os professores saberem o que acompanhar.")
        return dados

    def save(self, commit=True):
        aluno = super().save(commit=False)
        novo = aluno.pk is None
        if novo:
            aluno.criado_por = self.usuario

        # Atenção: guarda quando e por quem foi marcada.
        if self.cleaned_data.get("precisa_atencao"):
            aluno.precisa_atencao, aluno.motivo_atencao = self.atencao_antes
            aluno.marcar_atencao(self.cleaned_data["motivo_atencao"], self.usuario)
        else:
            aluno.desmarcar_atencao()

        if not commit:
            return aluno
        aluno.save()
        self.save_m2m()

        # Plano com IA: gera de novo quando ligado e as necessidades ou os formatos mudaram.
        if aluno.plano_ia:
            mudou = novo or not aluno.plano_ia_texto or {"necessidades", "formatos", "plano_ia"} & set(self.changed_data)
            if mudou:
                aluno.gerar_plano()
                aluno.save(update_fields=["plano_ia_texto", "plano_ia_gerado_em", "atualizado_em"])
        elif aluno.plano_ia_texto:
            aluno.limpar_plano()
            aluno.save(update_fields=["plano_ia_texto", "plano_ia_gerado_em", "atualizado_em"])
        return aluno


class AtencaoForm(forms.Form):
    """Ação rápida do perfil: marcar com motivo ou tirar da lista de atenção."""

    acao = forms.ChoiceField(choices=(("marcar", "Marcar"), ("desmarcar", "Desmarcar")))
    motivo = forms.CharField(label="Motivo", max_length=200, required=False)

    def clean(self):
        dados = super().clean()
        dados["motivo"] = (dados.get("motivo") or "").strip()
        if dados.get("acao") == "marcar" and not dados["motivo"]:
            self.add_error("motivo", "Diga o motivo, para os professores saberem o que acompanhar.")
        return dados
