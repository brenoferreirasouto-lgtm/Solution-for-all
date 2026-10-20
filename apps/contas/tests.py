from django.test import TestCase
from django.urls import reverse

from .models import Papel, Usuario


class UsuarioTests(TestCase):
    def test_cria_usuario_com_email_normalizado(self):
        usuario = Usuario.objects.create_user("Ana@Escola.COM", "senha-teste-1", nome="Ana")
        self.assertEqual(usuario.email, "ana@escola.com")
        self.assertEqual(usuario.papel, Papel.PROFESSOR)
        self.assertFalse(usuario.is_staff)

    def test_superusuario_e_coordenador(self):
        admin = Usuario.objects.create_superuser("admin@escola.com", "senha-teste-1", nome="Admin")
        self.assertTrue(admin.is_superuser)
        self.assertEqual(admin.papel, Papel.COORDENADOR)

    def test_nome_curto_mantem_o_titulo(self):
        self.assertEqual(Usuario(nome="Prof. Francisco Almeida").get_short_name(), "Prof. Francisco")
        self.assertEqual(Usuario(nome="Ana Beatriz").get_short_name(), "Ana")


class EntrarTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.usuario = Usuario.objects.create_user("prof@escola.com", "senha-teste-1", nome="Prof. Ana")

    def test_entra_com_email_e_senha(self):
        resposta = self.client.post(reverse("contas:entrar"), {"username": "prof@escola.com", "password": "senha-teste-1"})
        self.assertRedirects(resposta, reverse("painel:painel"))

    def test_senha_errada_mostra_erro(self):
        resposta = self.client.post(reverse("contas:entrar"), {"username": "prof@escola.com", "password": "errada"})
        self.assertContains(resposta, "E-mail ou senha incorretos.")

    def test_usuario_desativado_nao_entra(self):
        self.usuario.is_active = False
        self.usuario.save()
        resposta = self.client.post(reverse("contas:entrar"), {"username": "prof@escola.com", "password": "senha-teste-1"})
        self.assertEqual(resposta.status_code, 200)
        self.assertFalse(resposta.wsgi_request.user.is_authenticated)

    def test_sair_so_por_post(self):
        self.client.force_login(self.usuario)
        self.assertEqual(self.client.get(reverse("contas:sair")).status_code, 405)
        self.assertRedirects(self.client.post(reverse("contas:sair")), reverse("contas:entrar"))
