"""
Testes do esqueleto: toda rota existe e cada papel só entra onde pode.

Quando uma entrega trocar uma página "em construção" pela tela de verdade,
estes testes continuam valendo: a URL, o nome e as permissões não mudam.
"""

from django.test import TestCase
from django.urls import reverse

from apps.alunos.models import Aluno, TipoAdaptacao
from apps.contas.models import Papel, Usuario
from apps.escola.models import DiaSemana, Disciplina, HorarioAula, Lecionacao, Turma
from apps.materiais.models import Adaptacao, Material
from apps.materiais.services.ia import gerar_adaptacao

C, P, N = Papel.COORDENADOR, Papel.PROFESSOR, Papel.NUCLEO


class EsqueletoTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.coordenador = Usuario.objects.create_user("coord@teste.com", "senha-teste-1", nome="Coord", papel=C)
        cls.professor = Usuario.objects.create_user("prof@teste.com", "senha-teste-1", nome="Prof. Ana", papel=P)
        cls.outro_professor = Usuario.objects.create_user("prof2@teste.com", "senha-teste-1", nome="Prof. Beto", papel=P)
        cls.nucleo = Usuario.objects.create_user("nucleo@teste.com", "senha-teste-1", nome="Núcleo", papel=N)

        turma = Turma.objects.create(nome="7º B", ano_letivo=2026)
        disciplina = Disciplina.objects.create(nome="Ciências")
        lecionacao = Lecionacao.objects.create(professor=cls.professor, turma=turma, disciplina=disciplina)
        cls.horario = HorarioAula.objects.create(
            lecionacao=lecionacao, dia_semana=DiaSemana.SEGUNDA, hora_inicio="08:00", hora_fim="08:50"
        )

        cls.aluno = Aluno.objects.create(nome="Ana Beatriz", turma=turma)
        cls.aluno.professores.add(cls.professor)
        cls.aluno_de_outro = Aluno.objects.create(nome="Lucas Martins", turma=turma)
        cls.aluno_de_outro.professores.add(cls.outro_professor)

        tipo = TipoAdaptacao.objects.get(slug="simples")  # criado pela migration de catálogos
        cls.material = Material.objects.create(titulo="Fotossíntese", arquivo="materiais/aula.pdf", professor=cls.professor)
        cls.adaptacao = Adaptacao.objects.create(
            material=cls.material, aluno=cls.aluno, tipo=tipo, criado_por=cls.professor
        )

    def usuario(self, papel):
        return {C: self.coordenador, P: self.professor, N: self.nucleo}[papel]


# (nome da rota, kwargs, papéis que acessam) -- páginas GET
PAGINAS = [
    ("painel:painel", {}, (C, P, N)),
    ("alunos:lista", {}, (C, P, N)),
    ("alunos:novo", {}, (C,)),
    ("alunos:detalhe", {"pk": "aluno"}, (C, P, N)),
    ("alunos:editar", {"pk": "aluno"}, (C,)),
    ("escola:equipe", {}, (C,)),
    ("escola:professor_novo", {}, (C,)),
    ("escola:nucleo_novo", {}, (C,)),
    ("escola:membro_editar", {"pk": "professor"}, (C,)),
    ("escola:horarios", {}, (C,)),
    ("escola:horario_novo", {}, (C,)),
    ("escola:horario_editar", {"pk": "horario"}, (C,)),
    ("materiais:lista", {}, (C, P, N)),
    ("materiais:detalhe", {"pk": "material"}, (C, P, N)),
    ("materiais:adaptar", {}, (P,)),
    ("materiais:adaptacao", {"pk": "adaptacao"}, (C, P, N)),
    ("materiais:adaptacao_exportar", {"pk": "adaptacao"}, (C, P, N)),
]

# Ações que mudam dados: só POST
ACOES = [
    ("alunos:arquivar", {"pk": "aluno"}, (C,)),
    ("escola:membro_desativar", {"pk": "professor"}, (C,)),
    ("escola:horario_excluir", {"pk": "horario"}, (C,)),
    ("materiais:adaptacao_refazer", {"pk": "adaptacao"}, (P,)),
]

PUBLICAS = [
    "contas:entrar",
    "contas:senha_recuperar",
    "contas:senha_codigo",
    "contas:senha_nova",
    "core:privacidade",
    "core:termos",
]


class RotasTests(EsqueletoTestCase):
    def url(self, nome, kwargs):
        resolvidos = {k: getattr(self, v).pk for k, v in kwargs.items()}
        return reverse(nome, kwargs=resolvidos)

    def test_paginas_publicas_abrem_sem_login(self):
        for nome in PUBLICAS:
            with self.subTest(rota=nome):
                self.assertEqual(self.client.get(reverse(nome)).status_code, 200)

    def test_raiz_leva_ao_login_ou_ao_painel(self):
        self.assertRedirects(self.client.get("/"), reverse("contas:entrar"), fetch_redirect_response=False)
        self.client.force_login(self.professor)
        self.assertRedirects(self.client.get("/"), reverse("painel:painel"))

    def test_paginas_exigem_login(self):
        for nome, kwargs, _ in PAGINAS:
            with self.subTest(rota=nome):
                url = self.url(nome, kwargs)
                resposta = self.client.get(url)
                self.assertRedirects(resposta, f"{reverse('contas:entrar')}?next={url}", fetch_redirect_response=False)

    def test_cada_papel_so_entra_onde_pode(self):
        for papel in (C, P, N):
            self.client.force_login(self.usuario(papel))
            for nome, kwargs, papeis in PAGINAS:
                with self.subTest(papel=papel, rota=nome):
                    esperado = 200 if papel in papeis else 403
                    self.assertEqual(self.client.get(self.url(nome, kwargs)).status_code, esperado)

    def test_acoes_so_aceitam_post(self):
        for nome, kwargs, papeis in ACOES:
            self.client.force_login(self.usuario(papeis[0]))
            with self.subTest(rota=nome):
                self.assertEqual(self.client.get(self.url(nome, kwargs)).status_code, 405)

    def test_acoes_respeitam_o_papel(self):
        for papel in (C, P, N):
            self.client.force_login(self.usuario(papel))
            for nome, kwargs, papeis in ACOES:
                with self.subTest(papel=papel, rota=nome):
                    esperado = 302 if papel in papeis else 403
                    self.assertEqual(self.client.post(self.url(nome, kwargs)).status_code, esperado)

    def test_id_inexistente_da_404(self):
        self.client.force_login(self.coordenador)
        self.assertEqual(self.client.get(reverse("alunos:detalhe", kwargs={"pk": 9999})).status_code, 404)


class VisibilidadeTests(EsqueletoTestCase):
    def test_professor_nao_ve_aluno_de_outro_professor(self):
        self.client.force_login(self.professor)
        self.assertEqual(self.client.get(reverse("alunos:detalhe", kwargs={"pk": self.aluno.pk})).status_code, 200)
        self.assertEqual(
            self.client.get(reverse("alunos:detalhe", kwargs={"pk": self.aluno_de_outro.pk})).status_code, 404
        )

    def test_gestao_ve_todos_os_alunos(self):
        for usuario in (self.coordenador, self.nucleo):
            self.assertEqual(Aluno.objects.visiveis_para(usuario).count(), 2)
        self.assertEqual(list(Aluno.objects.visiveis_para(self.professor)), [self.aluno])

    def test_outro_professor_nao_ve_nem_refaz_adaptacao_alheia(self):
        self.client.force_login(self.outro_professor)
        url = reverse("materiais:adaptacao", kwargs={"pk": self.adaptacao.pk})
        self.assertEqual(self.client.get(url).status_code, 404)
        url = reverse("materiais:adaptacao_refazer", kwargs={"pk": self.adaptacao.pk})
        self.assertEqual(self.client.post(url).status_code, 404)


class MenuTests(EsqueletoTestCase):
    def test_menu_muda_pelo_papel(self):
        esperado = {
            C: ["Início", "Alunos", "Equipe", "Horários", "Materiais"],
            P: ["Início", "Meus alunos", "Adaptar material", "Materiais"],
            N: ["Início", "Alunos", "Materiais"],
        }
        for papel, rotulos in esperado.items():
            self.client.force_login(self.usuario(papel))
            resposta = self.client.get(reverse("painel:painel"))
            with self.subTest(papel=papel):
                self.assertEqual([i["rotulo"] for i in resposta.context["menu_itens"]], rotulos)

    def test_item_atual_marcado(self):
        self.client.force_login(self.professor)
        resposta = self.client.get(reverse("alunos:detalhe", kwargs={"pk": self.aluno.pk}))
        atuais = [i["rotulo"] for i in resposta.context["menu_itens"] if i["atual"]]
        self.assertEqual(atuais, ["Meus alunos"])


class DocumentosLegaisTests(EsqueletoTestCase):
    def test_documentos_abrem_sem_login_com_versao(self):
        for rota, titulo in (("core:termos", "Termos de Uso"), ("core:privacidade", "Política de Privacidade")):
            with self.subTest(rota=rota):
                resposta = self.client.get(reverse(rota))
                self.assertContains(resposta, f"<h1>{titulo}</h1>", html=True)
                self.assertContains(resposta, "Versão 1.0")
                self.assertContains(resposta, "23/10/2026")

    def test_login_avisa_e_linka_os_documentos(self):
        resposta = self.client.get(reverse("contas:entrar"))
        self.assertContains(resposta, "Ao entrar, você concorda com os")
        self.assertContains(resposta, f'href="{reverse("core:termos")}"')
        self.assertContains(resposta, f'href="{reverse("core:privacidade")}"')

    def test_menu_linka_os_documentos(self):
        self.client.force_login(self.professor)
        resposta = self.client.get(reverse("painel:painel"))
        self.assertContains(resposta, f'href="{reverse("core:termos")}"')
        self.assertContains(resposta, f'href="{reverse("core:privacidade")}"')

    def test_documentos_nao_tem_colchetes_do_rascunho(self):
        for rota in ("core:termos", "core:privacidade"):
            with self.subTest(rota=rota):
                texto = self.client.get(reverse(rota)).content.decode()
                self.assertNotIn("[", texto.split("<article>")[1].split("</article>")[0])


class IaSimuladaTests(EsqueletoTestCase):
    def test_gera_texto_marcado_como_simulado(self):
        tipo = TipoAdaptacao.objects.get(slug="resumo")
        resultado = gerar_adaptacao("As plantas usam a luz do sol.", tipo)
        self.assertEqual(resultado.gerado_por, "simulada")
        self.assertIn("As plantas usam a luz do sol.", resultado.conteudo)
        self.assertIn("Resumo", resultado.conteudo)
