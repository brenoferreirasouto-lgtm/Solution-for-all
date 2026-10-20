from django.contrib import admin

from .models import Disciplina, HorarioAula, Lecionacao, Turma


@admin.register(Turma)
class TurmaAdmin(admin.ModelAdmin):
    list_display = ("nome", "ano_letivo", "ativo")
    list_filter = ("ano_letivo", "ativo")
    search_fields = ("nome",)


@admin.register(Disciplina)
class DisciplinaAdmin(admin.ModelAdmin):
    search_fields = ("nome",)


class HorarioInline(admin.TabularInline):
    model = HorarioAula
    extra = 0


@admin.register(Lecionacao)
class LecionacaoAdmin(admin.ModelAdmin):
    list_display = ("disciplina", "turma", "professor")
    list_filter = ("turma", "disciplina")
    inlines = [HorarioInline]


@admin.register(HorarioAula)
class HorarioAulaAdmin(admin.ModelAdmin):
    list_display = ("dia_semana", "hora_inicio", "hora_fim", "lecionacao")
    list_filter = ("dia_semana",)
