from django.contrib import admin

from .models import Aluno, Necessidade, TipoAdaptacao


@admin.register(Necessidade)
class NecessidadeAdmin(admin.ModelAdmin):
    list_display = ("nome", "slug", "ordem")
    prepopulated_fields = {"slug": ("nome",)}


@admin.register(TipoAdaptacao)
class TipoAdaptacaoAdmin(admin.ModelAdmin):
    list_display = ("nome", "slug", "ordem")
    prepopulated_fields = {"slug": ("nome",)}


@admin.register(Aluno)
class AlunoAdmin(admin.ModelAdmin):
    list_display = ("nome", "turma", "precisa_atencao", "ativo")
    list_filter = ("turma", "necessidades", "precisa_atencao", "ativo")
    search_fields = ("nome",)
    filter_horizontal = ("necessidades", "formatos", "professores")
    # Preenchidos pelo app (Plano com IA e marcação de atenção), não à mão.
    readonly_fields = ("plano_ia_texto", "plano_ia_gerado_em", "atencao_marcada_em", "atencao_marcada_por", "criado_por")
