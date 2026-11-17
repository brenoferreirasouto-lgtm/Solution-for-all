"""
Tela Adaptar material (entrega #7) e revisão do texto gerado (entrega #8).

Os 3 passos do protótipo: 1. Aluno, 2. Conteúdo (arquivo, texto colado ou um
material já enviado) e 3. Formato. O formato do perfil do aluno já vem marcado.
"""

from django import forms

from apps.alunos.models import Aluno, TipoAdaptacao

from .models import Material
from .services.texto import ACEITA, LIMITE_ARQUIVO_MB, TextoIlegivel, extrair_texto, normalizar, titulo_sugerido

LIMITE_TEXTO = 30000  # caracteres colados na tela (cerca de 10 páginas)


class AlunoSelect(forms.Select):
    """Cada aluno leva os formatos do perfil, para a tela marcar o formato ao trocar de aluno."""

    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):
        opcao = super().create_option(name, value, label, selected, index, subindex, attrs)
        aluno = getattr(value, "instance", None)
        if aluno is not None:
            opcao["attrs"]["data-formatos"] = ",".join(str(f.pk) for f in aluno.formatos.all())
        return opcao


class AlunoChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, aluno):
        return f"{aluno.nome} · {aluno.turma.nome}"


class MaterialChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, material):
        return f"{material.titulo} · {material.criado_em:%d/%m/%Y}"


class AdaptarForm(forms.Form):
    ARQUIVO, TEXTO, MATERIAL = "arquivo", "texto", "material"
    ORIGENS = ((ARQUIVO, "Enviar arquivo"), (TEXTO, "Colar texto"), (MATERIAL, "Material já enviado"))

    aluno = AlunoChoiceField(
        label="Para qual aluno?", queryset=Aluno.objects.none(), empty_label="Selecione o aluno", widget=AlunoSelect
    )
    origem = forms.ChoiceField(label="Como enviar o conteúdo", choices=ORIGENS, initial=ARQUIVO, widget=forms.RadioSelect)
    arquivo = forms.FileField(
        label="Arquivo",
        required=False,
        help_text=f"PDF, Word (.docx) ou .txt, até {LIMITE_ARQUIVO_MB} MB. PDF escaneado (foto) não tem texto para ler.",
        widget=forms.FileInput(attrs={"accept": ACEITA}),
    )
    texto = forms.CharField(
        label="Texto do material",
        required=False,
        max_length=LIMITE_TEXTO,
        widget=forms.Textarea(attrs={"rows": 8}),
        help_text="Cole aqui o conteúdo da aula.",
    )
    material = MaterialChoiceField(
        label="Material", required=False, queryset=Material.objects.none(), empty_label="Selecione o material"
    )
    titulo = forms.CharField(
        label="Título do material",
        required=False,
        max_length=200,
        help_text="Opcional. Se ficar em branco, usamos o nome do arquivo ou a primeira linha do texto.",
    )
    tipo = forms.ModelChoiceField(
        label="Formato",
        queryset=TipoAdaptacao.objects.all(),
        empty_label=None,
        widget=forms.RadioSelect,
        error_messages={"required": "Escolha o formato da adaptação."},
    )

    def __init__(self, *args, usuario, **kwargs):
        super().__init__(*args, **kwargs)
        self.usuario = usuario
        self.fields["aluno"].queryset = (
            Aluno.objects.visiveis_para(usuario)
            .filter(ativo=True)
            .select_related("turma")
            .prefetch_related("formatos")
            .order_by("nome")
        )
        self.fields["material"].queryset = Material.objects.filter(professor=usuario).order_by("-criado_em")
        self.tem_materiais = self.fields["material"].queryset.exists()
        if not self.tem_materiais:
            self.fields["origem"].choices = self.ORIGENS[:2]

    def clean(self):
        dados = super().clean()
        origem = dados.get("origem")
        dados["texto_final"] = ""
        dados["titulo_final"] = (dados.get("titulo") or "").strip()

        if origem == self.ARQUIVO:
            arquivo = dados.get("arquivo")
            if not arquivo:
                self.add_error("arquivo", "Escolha o arquivo do material.")
            else:
                try:
                    dados["texto_final"] = extrair_texto(arquivo)
                except TextoIlegivel as erro:
                    self.add_error("arquivo", str(erro))
                else:
                    dados["titulo_final"] = dados["titulo_final"] or titulo_sugerido(arquivo.name, dados["texto_final"])
        elif origem == self.TEXTO:
            texto = normalizar(dados.get("texto"))
            if not texto and "texto" not in self.errors:
                self.add_error("texto", "Cole o texto do material.")
            dados["texto_final"] = texto
            dados["titulo_final"] = dados["titulo_final"] or titulo_sugerido(texto=texto)
        elif origem == self.MATERIAL:
            if not dados.get("material") and "material" not in self.errors:
                self.add_error("material", "Escolha um dos seus materiais.")
        return dados


class RevisarForm(forms.Form):
    """O professor corrige o texto gerado e salva (botão Salvar do protótipo)."""

    conteudo = forms.CharField(
        label="Texto adaptado",
        max_length=LIMITE_TEXTO,
        widget=forms.Textarea(attrs={"rows": 14}),
        error_messages={"required": "O texto não pode ficar vazio. Use Refazer para gerar de novo."},
    )

    def clean_conteudo(self):
        conteudo = (self.cleaned_data["conteudo"] or "").replace("\r\n", "\n").strip()
        if not conteudo:
            raise forms.ValidationError("O texto não pode ficar vazio. Use Refazer para gerar de novo.")
        return conteudo
