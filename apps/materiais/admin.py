from django.contrib import admin

from .models import Adaptacao, Material


@admin.register(Material)
class MaterialAdmin(admin.ModelAdmin):
    list_display = ("titulo", "professor", "disciplina", "criado_em")
    list_filter = ("disciplina",)
    search_fields = ("titulo",)


@admin.register(Adaptacao)
class AdaptacaoAdmin(admin.ModelAdmin):
    list_display = ("material", "aluno", "tipo", "versao", "status", "gerado_por", "criado_em")
    list_filter = ("status", "tipo", "gerado_por")
