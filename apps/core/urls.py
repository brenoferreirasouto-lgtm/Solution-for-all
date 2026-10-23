from django.urls import path

from . import views

app_name = "core"

urlpatterns = [
    path("privacidade/", views.PrivacidadeView.as_view(), name="privacidade"),
    path("termos/", views.TermosView.as_view(), name="termos"),
]
