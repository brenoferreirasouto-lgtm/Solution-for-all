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


class AcessoAosCatalogosTests(TestCase):
    """Coordenador e núcleo (mesmo os cadastrados depois) entram nos Catálogos; professor não."""

    CATALOGOS = ["escola.turma", "escola.disciplina", "alunos.necessidade", "alunos.tipoadaptacao", "alunos.aluno"]

    def criar(self, papel, email="x@escola.com"):
        return Usuario.objects.create_user(email, "senha-teste-1", nome="Fulano", papel=papel)

    def test_is_staff_segue_o_papel(self):
        self.assertTrue(self.criar(Papel.COORDENADOR, "c@escola.com").is_staff)
        self.assertTrue(self.criar(Papel.NUCLEO, "n@escola.com").is_staff)
        self.assertFalse(self.criar(Papel.PROFESSOR, "p@escola.com").is_staff)

    def test_trocar_o_papel_atualiza_is_staff(self):
        usuario = self.criar(Papel.PROFESSOR)
        usuario.papel = Papel.NUCLEO
        usuario.save()
        self.assertTrue(Usuario.objects.get(pk=usuario.pk).is_staff)
        usuario.papel = Papel.PROFESSOR
        usuario.save()
        self.assertFalse(Usuario.objects.get(pk=usuario.pk).is_staff)

    def test_coordenador_novo_faz_tudo_nos_catalogos(self):
        coordenador = self.criar(Papel.COORDENADOR)
        self.assertFalse(coordenador.is_superuser)
        for modelo in self.CATALOGOS:
            app, nome = modelo.split(".")
            for acao in ("view", "add", "change", "delete"):
                with self.subTest(modelo=modelo, acao=acao):
                    self.assertTrue(coordenador.has_perm(f"{app}.{acao}_{nome}"))

    def test_nucleo_cadastra_e_edita_mas_nao_exclui(self):
        nucleo = self.criar(Papel.NUCLEO)
        for modelo in self.CATALOGOS:
            app, nome = modelo.split(".")
            with self.subTest(modelo=modelo):
                for acao in ("view", "add", "change"):
                    self.assertTrue(nucleo.has_perm(f"{app}.{acao}_{nome}"))
                self.assertFalse(nucleo.has_perm(f"{app}.delete_{nome}"))

    def test_professor_nao_tem_permissao_de_catalogo(self):
        professor = self.criar(Papel.PROFESSOR)
        self.assertFalse(professor.has_perm("alunos.add_aluno"))
        self.assertFalse(professor.has_module_perms("alunos"))

    def test_ninguem_mexe_em_usuarios_pelo_admin_sem_ser_superusuario(self):
        for papel in (Papel.COORDENADOR, Papel.NUCLEO):
            usuario = self.criar(papel, f"{papel}@escola.com")
            self.assertFalse(usuario.has_perm("contas.change_usuario"))
            self.assertFalse(usuario.has_perm("auth.change_group"))

    def test_usuario_desativado_perde_o_acesso(self):
        coordenador = self.criar(Papel.COORDENADOR)
        coordenador.is_active = False
        self.assertFalse(coordenador.has_perm("alunos.add_aluno"))

    def test_admin_abre_para_coordenador_e_nucleo_e_fecha_para_professor(self):
        esperado = {Papel.COORDENADOR: 200, Papel.NUCLEO: 200, Papel.PROFESSOR: 302}
        for papel, status in esperado.items():
            self.client.force_login(self.criar(papel, f"{papel}@escola.com"))
            with self.subTest(papel=papel):
                self.assertEqual(self.client.get("/admin/").status_code, status)
                if status == 200:
                    self.assertEqual(self.client.get("/admin/alunos/aluno/").status_code, 200)
                    self.assertEqual(self.client.get("/admin/alunos/aluno/add/").status_code, 200)
                    self.assertEqual(self.client.get("/admin/escola/turma/add/").status_code, 200)
                    self.assertEqual(self.client.get("/admin/alunos/necessidade/add/").status_code, 200)
                    self.assertEqual(self.client.get("/admin/contas/usuario/").status_code, 403)

    def test_nucleo_exclui_e_recebe_403(self):
        self.client.force_login(self.criar(Papel.NUCLEO))
        from apps.escola.models import Disciplina

        disciplina = Disciplina.objects.create(nome="História")
        resposta = self.client.get(f"/admin/escola/disciplina/{disciplina.pk}/delete/")
        self.assertEqual(resposta.status_code, 403)

    def test_menu_mostra_catalogos_para_coordenador_e_nucleo(self):
        for papel, aparece in ((Papel.COORDENADOR, True), (Papel.NUCLEO, True), (Papel.PROFESSOR, False)):
            self.client.force_login(self.criar(papel, f"{papel}@escola.com"))
            resposta = self.client.get(reverse("painel:painel"))
            with self.subTest(papel=papel):
                self.assertEqual(resposta.context["mostrar_catalogos"], aparece)
