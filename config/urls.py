"""Rotas do Solution for All. Cada app tem o seu urls.py com namespace."""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

admin.site.site_header = "Solution for All · Catálogos"
admin.site.site_title = "Solution for All"
admin.site.index_title = "Turmas, matérias, necessidades e formatos"

urlpatterns = [
    path("", include("apps.painel.urls")),
    path("", include("apps.contas.urls")),
    path("", include("apps.core.urls")),
    path("alunos/", include("apps.alunos.urls")),
    path("", include("apps.escola.urls")),
    path("", include("apps.materiais.urls")),
    path("admin/", admin.site.urls),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
