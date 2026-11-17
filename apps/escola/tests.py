"""Entregas #3 e #4 (equipe) e #6 (horários das aulas)."""

from django.test import TestCase
from django.urls import reverse

from apps.alunos.models import Aluno
from apps.contas.models import Papel, Usuario

from .models import DiaSemana, Disciplina, HorarioAula, Lecionacao, Turma

SENHA = "senha-forte-9X"


class EquipeBase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.coord = Usuario.objects.create_user("coord@teste.com", "senha-teste-1", nome="Coord", papel=Papel.COORDENADOR)
        cls.prof = Usuario.objects.create_user("prof@teste.com", "senha-teste-1", nome="Prof. Ana", papel=Papel.PROFESSOR)
        cls.turma = Turma.objects.create(nome="7º B", ano_letivo=2026)
        cls.disciplina = Disciplina.objects.create(nome="Ciências")
        cls.aluno = Aluno.objects.create(nome="Ana Beatriz", turma=cls.turma)

    def setUp(self):
        self.client.force_login(self.coord)

    def dados(self, nome, email, **extra):
        return {"nome": nome, "email": email, "senha1": SENHA, "senha2": SENHA, **extra}


class CadastroTests(EquipeBase):
    def test_cadastra_coordenador_com_acesso_aos_catalogos(self):
        resposta = self.client.post(reverse("escola:coordenador_novo"), self.dados("Bia", "Bia@Escola.com"))
        self.assertRedirects(resposta, reverse("escola:equipe"))
        novo = Usuario.objects.get(email="bia@escola.com")
        self.assertEqual(novo.papel, Papel.COORDENADOR)
        self.assertTrue(novo.is_staff)
        self.assertFalse(novo.is_superuser)

        # Entra com a senha que a coordenação definiu e abre os catálogos.
        self.client.logout()
        self.assertTrue(self.client.login(username="bia@escola.com", password=SENHA))
        self.assertEqual(self.client.get("/admin/").status_code, 200)
        self.assertEqual(self.client.get("/admin/alunos/aluno/add/").status_code, 200)
        self.assertEqual(self.client.get(reverse("escola:equipe")).status_code, 200)

    def test_cadastra_membro_do_nucleo_que_cadastra_nos_catalogos(self):
        self.client.post(reverse("escola:nucleo_novo"), self.dados("Carla", "carla@escola.com"))
        novo = Usuario.objects.get(email="carla@escola.com")
        self.assertEqual(novo.papel, Papel.NUCLEO)

        self.client.logout()
        self.client.login(username="carla@escola.com", password=SENHA)
        self.assertEqual(self.client.get("/admin/").status_code, 200)
        resposta = self.client.post(
            "/admin/escola/disciplina/add/", {"nome": "Geografia"}, follow=False
        )
        self.assertEqual(resposta.status_code, 302)
        self.assertTrue(Disciplina.objects.filter(nome="Geografia").exists())
        # O núcleo não acessa a equipe (tela da coordenação).
        self.assertEqual(self.client.get(reverse("escola:equipe")).status_code, 403)

    def test_cadastra_professor_com_turma_materia_e_alunos(self):
        dados = self.dados(
            "Prof. Beto", "beto@escola.com",
            turmas=[self.turma.pk], disciplina=self.disciplina.pk, alunos=[self.aluno.pk],
        )
        self.assertRedirects(self.client.post(reverse("escola:professor_novo"), dados), reverse("escola:equipe"))
        novo = Usuario.objects.get(email="beto@escola.com")
        self.assertEqual(novo.papel, Papel.PROFESSOR)
        self.assertFalse(novo.is_staff)
        self.assertTrue(Lecionacao.objects.filter(professor=novo, turma=self.turma, disciplina=self.disciplina).exists())
        self.assertEqual(list(Aluno.objects.visiveis_para(novo)), [self.aluno])

        self.client.logout()
        self.client.login(username="beto@escola.com", password=SENHA)
        self.assertEqual(self.client.get("/admin/").status_code, 302)  # professor não vê catálogos

    def test_papel_nao_pode_ser_forcado_pelo_formulario(self):
        self.client.post(reverse("escola:professor_novo"), self.dados("Fulano", "f@escola.com", papel="COORDENADOR"))
        self.assertEqual(Usuario.objects.get(email="f@escola.com").papel, Papel.PROFESSOR)

    def test_email_repetido_e_recusado_sem_diferenciar_maiusculas(self):
        resposta = self.client.post(reverse("escola:nucleo_novo"), self.dados("Outra", "PROF@teste.com"))
        self.assertContains(resposta, "Já existe uma pessoa cadastrada com este e-mail.")
        self.assertEqual(Usuario.objects.filter(email__iexact="prof@teste.com").count(), 1)

    def test_senhas_diferentes_ou_fracas_sao_recusadas(self):
        dados = self.dados("Dani", "dani@escola.com", senha2="outra-coisa")
        self.assertContains(self.client.post(reverse("escola:nucleo_novo"), dados), "As senhas não são iguais.")
        dados = self.dados("Dani", "dani@escola.com", senha1="12345678", senha2="12345678")
        self.assertEqual(self.client.post(reverse("escola:nucleo_novo"), dados).status_code, 200)
        self.assertFalse(Usuario.objects.filter(email="dani@escola.com").exists())

    def test_professor_com_turma_exige_materia(self):
        resposta = self.client.post(
            reverse("escola:professor_novo"), self.dados("Eva", "eva@escola.com", turmas=[self.turma.pk])
        )
        self.assertContains(resposta, "Escolha a matéria")
        self.assertFalse(Usuario.objects.filter(email="eva@escola.com").exists())

    def test_so_a_coordenacao_cadastra(self):
        for papel in (Papel.PROFESSOR, Papel.NUCLEO):
            usuario = Usuario.objects.create_user(f"{papel}@x.com", "senha-teste-1", nome="X", papel=papel)
            self.client.force_login(usuario)
            for rota in ("escola:coordenador_novo", "escola:professor_novo", "escola:nucleo_novo"):
                with self.subTest(papel=papel, rota=rota):
                    self.assertEqual(self.client.post(reverse(rota), self.dados("Z", "z@x.com")).status_code, 403)
        self.assertFalse(Usuario.objects.filter(email="z@x.com").exists())


class EdicaoTests(EquipeBase):
    def test_equipe_lista_os_tres_papeis(self):
        nucleo = Usuario.objects.create_user("n@teste.com", "senha-teste-1", nome="Nina Núcleo", papel=Papel.NUCLEO)
        resposta = self.client.get(reverse("escola:equipe"))
        for pessoa in (self.coord, self.prof, nucleo):
            self.assertContains(resposta, pessoa.email)

    def test_edita_nome_sem_mexer_na_senha(self):
        url = reverse("escola:membro_editar", kwargs={"pk": self.prof.pk})
        dados = {"nome": "Prof. Ana Maria", "email": "prof@teste.com", "senha1": "", "senha2": ""}
        self.assertRedirects(self.client.post(url, dados), reverse("escola:equipe"))
        self.prof.refresh_from_db()
        self.assertEqual(self.prof.nome, "Prof. Ana Maria")
        self.assertTrue(self.prof.check_password("senha-teste-1"))

    def test_edicao_troca_a_senha_e_os_alunos_do_professor(self):
        url = reverse("escola:membro_editar", kwargs={"pk": self.prof.pk})
        dados = self.dados("Prof. Ana", "prof@teste.com", alunos=[self.aluno.pk])
        self.client.post(url, dados)
        self.prof.refresh_from_db()
        self.assertTrue(self.prof.check_password(SENHA))
        self.assertEqual(list(self.prof.alunos_acompanhados.all()), [self.aluno])

    def test_editar_coordenador_mantem_o_papel(self):
        url = reverse("escola:membro_editar", kwargs={"pk": self.coord.pk})
        self.client.post(url, {"nome": "Coord 2", "email": "coord@teste.com", "senha1": "", "senha2": ""})
        self.coord.refresh_from_db()
        self.assertEqual((self.coord.nome, self.coord.papel, self.coord.is_staff), ("Coord 2", Papel.COORDENADOR, True))

    def test_desativar_e_reativar(self):
        url = reverse("escola:membro_desativar", kwargs={"pk": self.prof.pk})
        self.client.post(url)
        self.prof.refresh_from_db()
        self.assertFalse(self.prof.is_active)
        # Desativado, não entra mais.
        self.client.logout()
        resposta = self.client.post(reverse("contas:entrar"), {"username": "prof@teste.com", "password": "senha-teste-1"})
        self.assertFalse(resposta.wsgi_request.user.is_authenticated)
        # Reativa.
        self.client.force_login(self.coord)
        self.client.post(url)
        self.prof.refresh_from_db()
        self.assertTrue(self.prof.is_active)

    def test_coordenador_nao_desativa_o_proprio_acesso(self):
        self.client.post(reverse("escola:membro_desativar", kwargs={"pk": self.coord.pk}))
        self.coord.refresh_from_db()
        self.assertTrue(self.coord.is_active)


class HorariosTests(EquipeBase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.prof2 = Usuario.objects.create_user("prof2@teste.com", "senha-teste-1", nome="Prof. Beto", papel=Papel.PROFESSOR)
        cls.turma2 = Turma.objects.create(nome="8º A", ano_letivo=2026)
        cls.matematica = Disciplina.objects.create(nome="Matemática")

    def aula(self, **extra):
        dados = {
            "turma": self.turma.pk,
            "disciplina": self.disciplina.pk,
            "professor": self.prof.pk,
            "dia_semana": DiaSemana.SEGUNDA,
            "hora_inicio": "08:00",
            "hora_fim": "08:50",
        }
        dados.update(extra)
        return self.client.post(reverse("escola:horario_novo"), dados)

    def test_cadastra_horario_e_cria_a_lecionacao(self):
        resposta = self.aula()
        self.assertRedirects(resposta, f"{reverse('escola:horarios')}?turma={self.turma.pk}")
        horario = HorarioAula.objects.get()
        self.assertEqual(
            (horario.lecionacao.professor, horario.lecionacao.turma, horario.lecionacao.disciplina),
            (self.prof, self.turma, self.disciplina),
        )
        # Uma segunda aula da mesma matéria reaproveita a lecionação.
        self.aula(dia_semana=DiaSemana.QUARTA)
        self.assertEqual(Lecionacao.objects.count(), 1)
        self.assertEqual(HorarioAula.objects.count(), 2)

    def test_fim_antes_do_inicio_e_recusado(self):
        resposta = self.aula(hora_inicio="09:00", hora_fim="08:00")
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.context["form"].errors["hora_fim"], ["O fim precisa ser depois do início."])
        self.assertFalse(HorarioAula.objects.exists())

    def test_turma_nao_tem_duas_aulas_no_mesmo_horario(self):
        self.aula()
        resposta = self.aula(professor=self.prof2.pk, disciplina=self.matematica.pk, hora_inicio="08:30", hora_fim="09:20")
        self.assertEqual(resposta.status_code, 200)
        self.assertIn("A turma 7º B já tem Ciências nesse horário", resposta.context["form"].non_field_errors()[0])
        self.assertEqual(HorarioAula.objects.count(), 1)

    def test_professor_nao_da_duas_aulas_ao_mesmo_tempo(self):
        self.aula()
        resposta = self.aula(turma=self.turma2.pk, hora_inicio="07:30", hora_fim="08:10")
        self.assertEqual(resposta.status_code, 200)
        self.assertIn("Prof. Ana já dá aula nesse horário", resposta.context["form"].non_field_errors()[0])

    def test_aulas_seguidas_e_outro_dia_sao_permitidas(self):
        self.aula()
        self.assertEqual(self.aula(hora_inicio="08:50", hora_fim="09:40").status_code, 302)  # começa quando a outra acaba
        self.assertEqual(self.aula(dia_semana=DiaSemana.TERCA).status_code, 302)
        self.assertEqual(HorarioAula.objects.count(), 3)

    def test_editar_nao_conflita_com_ele_mesmo(self):
        self.aula()
        horario = HorarioAula.objects.get()
        dados = {
            "turma": self.turma.pk,
            "disciplina": self.matematica.pk,
            "professor": self.prof.pk,
            "dia_semana": DiaSemana.SEGUNDA,
            "hora_inicio": "08:00",
            "hora_fim": "09:00",
        }
        resposta = self.client.post(reverse("escola:horario_editar", kwargs={"pk": horario.pk}), dados)
        self.assertEqual(resposta.status_code, 302)
        horario.refresh_from_db()
        self.assertEqual(horario.lecionacao.disciplina, self.matematica)
        self.assertEqual(f"{horario.hora_fim:%H:%M}", "09:00")

    def test_excluir_so_por_post(self):
        self.aula()
        horario = HorarioAula.objects.get()
        url = reverse("escola:horario_excluir", kwargs={"pk": horario.pk})
        self.assertEqual(self.client.get(url).status_code, 405)
        self.assertRedirects(self.client.post(url), f"{reverse('escola:horarios')}?turma={self.turma.pk}")
        self.assertFalse(HorarioAula.objects.exists())

    def test_grade_filtra_por_turma(self):
        self.aula()
        self.aula(turma=self.turma2.pk, professor=self.prof2.pk, dia_semana=DiaSemana.TERCA)
        resposta = self.client.get(reverse("escola:horarios"))
        self.assertEqual(resposta.context["total"], 2)
        resposta = self.client.get(reverse("escola:horarios"), {"turma": self.turma2.pk})
        self.assertEqual(resposta.context["total"], 1)
        self.assertContains(resposta, "Prof. Beto")
        self.assertNotContains(resposta, "Prof. Ana")

    def test_so_a_coordenacao_cuida_dos_horarios(self):
        nucleo = Usuario.objects.create_user("nucleo@teste.com", "senha-teste-1", nome="Núcleo", papel=Papel.NUCLEO)
        for usuario in (self.prof, nucleo):
            self.client.force_login(usuario)
            self.assertEqual(self.client.get(reverse("escola:horarios")).status_code, 403)
            self.assertEqual(self.aula().status_code, 403)
        self.assertFalse(HorarioAula.objects.exists())

    def test_aulas_de_hoje(self):
        self.aula(dia_semana=DiaSemana.SEGUNDA)
        self.aula(dia_semana=DiaSemana.TERCA)
        self.assertEqual(HorarioAula.objects.do_dia(DiaSemana.TERCA).count(), 1)
