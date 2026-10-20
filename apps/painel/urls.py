from django.urls import path

from . import views

app_name = "painel"

urlpatterns = [
    path("", views.inicio, name="inicio"),
    path("painel/", views.PainelView.as_view(), name="painel"),
]
