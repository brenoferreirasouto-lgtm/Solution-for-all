"""Entrega #5 (alunos e perfil cognitivo) e entrega #6 (alunos que precisam de atenção)."""

from django.test import TestCase
from django.urls import reverse

from apps.contas.models import Papel, Usuario
from apps.escola.models import Turma

from .models import Aluno, Necessidade, TipoAdaptacao


class AlunosBase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.coord = Usuario.objects.create_user("coord@teste.com", "senha-teste-1", nome="Coord", papel=Papel.COORDENADOR)
        cls.nucleo = Usuario.objects.create_user("nucleo@teste.com", "senha-teste-1", nome="Núcleo", papel=Papel.NUCLEO)
        cls.prof = Usuario.objects.create_user("prof@teste.com", "senha-teste-1", nome="Prof. Ana", papel=Papel.PROFESSOR)
        cls.outro_prof = Usuario.objects.create_user("prof2@teste.com", "senha-teste-1", nome="Prof. Beto", papel=Papel.PROFESSOR)
        cls.turma = Turma.objects.create(nome="7º B", ano_letivo=2026)
        cls.turma_antiga = Turma.objects.create(nome="6º A", ano_letivo=2025, ativo=False)
        # Catálogos criados pela migration 0002.
        cls.tea = Necessidade.objects.get(slug="tea")
        cls.tdah = Necessidade.objects.get(slug="tdah")
        cls.simples = TipoAdaptacao.objects.get(slug="simples")
        cls.visual = TipoAdaptacao.objects.get(slug="visual")

    def dados(self, **extra):
        base = {
            "nome": "  Beatriz   Lima ",
            "turma": self.turma.pk,
            "necessidades": [self.tea.pk],
            "formatos": [self.simples.pk],
            "como_aprende": "Com exemplos visuais.",
            "dificuldades": "Textos longos.",
            "estrategias": "Dividir em etapas.",
            "observacoes": "",
            "professores": [self.prof.pk],
            "motivo_atencao": "",
        }
        base.update(extra)
        return base

    def criar(self, usuario=None, **extra):
        self.client.force_login(usuario or self.coord)
        resposta = self.client.post(reverse("alunos:novo"), self.dados(**extra))
        return resposta, Aluno.objects.order_by("-pk").first()


class CadastroTests(AlunosBase):
    def test_coordenacao_cadastra_aluno_com_perfil_cognitivo(self):
        resposta, aluno = self.criar()
        self.assertRedirects(resposta, reverse("alunos:detalhe", kwargs={"pk": aluno.pk}))
        self.assertEqual(aluno.nome, "Beatriz Lima")
        self.assertEqual(aluno.turma, self.turma)
        self.assertEqual(list(aluno.necessidades.all()), [self.tea])
        self.assertEqual(list(aluno.formatos.all()), [self.simples])
        self.assertEqual(aluno.como_aprende, "Com exemplos visuais.")
        self.assertEqual(aluno.dificuldades, "Textos longos.")
        self.assertEqual(aluno.estrategias, "Dividir em etapas.")
        self.assertEqual(aluno.criado_por, self.coord)
        # O professor marcado passa a enxergar o aluno; o outro, não.
        self.assertIn(aluno, Aluno.objects.visiveis_para(self.prof))
        self.assertNotIn(aluno, Aluno.objects.visiveis_para(self.outro_prof))

    def test_nucleo_tambem_cadastra_e_edita(self):
        resposta, aluno = self.criar(usuario=self.nucleo)
        self.assertEqual(resposta.status_code, 302)
        self.assertEqual(aluno.criado_por, self.nucleo)
        resposta = self.client.post(
            reverse("alunos:editar", kwargs={"pk": aluno.pk}), self.dados(estrategias="Avisar antes das mudanças.")
        )
        self.assertEqual(resposta.status_code, 302)
        aluno.refresh_from_db()
        self.assertEqual(aluno.estrategias, "Avisar antes das mudanças.")

    def test_professor_nao_cadastra_nem_edita(self):
        aluno = Aluno.objects.create(nome="Lucas", turma=self.turma)
        self.client.force_login(self.prof)
        self.assertEqual(self.client.post(reverse("alunos:novo"), self.dados()).status_code, 403)
        self.assertEqual(self.client.post(reverse("alunos:editar", kwargs={"pk": aluno.pk}), self.dados()).status_code, 403)
        self.assertFalse(Aluno.objects.filter(nome="Beatriz Lima").exists())

    def test_turma_e_obrigatoria_e_turma_inativa_nao_aparece(self):
        resposta, _ = self.criar(turma="")
        self.assertEqual(resposta.status_code, 200)
        self.assertFalse(Aluno.objects.exists())
        self.assertNotIn(self.turma_antiga, resposta.context["form"].fields["turma"].queryset)

    def test_perfil_mostra_os_dados_e_professor_so_abre_os_seus(self):
        _, aluno = self.criar()
        self.client.force_login(self.prof)
        resposta = self.client.get(reverse("alunos:detalhe", kwargs={"pk": aluno.pk}))
        self.assertContains(resposta, "Com exemplos visuais.")
        self.assertContains(resposta, "Dividir em etapas.")
        self.assertNotContains(resposta, "Editar perfil")  # professor só lê
        self.client.force_login(self.outro_prof)
        self.assertEqual(self.client.get(reverse("alunos:detalhe", kwargs={"pk": aluno.pk})).status_code, 404)


class PlanoComIATests(AlunosBase):
    def test_plano_gera_sugestoes_sem_o_nome_e_sem_o_perfil_escrito(self):
        _, aluno = self.criar(plano_ia="on", necessidades=[self.tea.pk, self.tdah.pk], formatos=[self.visual.pk])
        self.assertTrue(aluno.plano_ia)
        self.assertIsNotNone(aluno.plano_ia_gerado_em)
        self.assertIn("TEA", aluno.plano_ia_texto)
        self.assertIn("TDAH", aluno.plano_ia_texto)
        self.assertIn("Visual", aluno.plano_ia_texto)
        # Regra do projeto: a IA nunca recebe o nome nem o que a escola escreveu sobre o aluno.
        self.assertNotIn("Beatriz", aluno.plano_ia_texto)
        self.assertNotIn("Com exemplos visuais", aluno.plano_ia_texto)

    def test_plano_acompanha_as_necessidades_e_some_quando_desligado(self):
        _, aluno = self.criar(plano_ia="on")
        url = reverse("alunos:editar", kwargs={"pk": aluno.pk})
        self.client.post(url, self.dados(plano_ia="on", necessidades=[self.tdah.pk]))
        aluno.refresh_from_db()
        self.assertIn("TDAH", aluno.plano_ia_texto)
        self.assertNotIn("TEA", aluno.plano_ia_texto)

        self.client.post(url, self.dados(necessidades=[self.tdah.pk]))  # desmarca o plano
        aluno.refresh_from_db()
        self.assertFalse(aluno.plano_ia)
        self.assertEqual(aluno.plano_ia_texto, "")
        self.assertIsNone(aluno.plano_ia_gerado_em)

    def test_gerar_de_novo_pelo_perfil(self):
        _, aluno = self.criar(plano_ia="on")
        Aluno.objects.filter(pk=aluno.pk).update(plano_ia_texto="antigo")
        self.client.post(reverse("alunos:plano", kwargs={"pk": aluno.pk}))
        aluno.refresh_from_db()
        self.assertIn("TEA", aluno.plano_ia_texto)

    def test_gerar_com_plano_desligado_nao_faz_nada(self):
        _, aluno = self.criar()
        self.client.post(reverse("alunos:plano", kwargs={"pk": aluno.pk}))
        aluno.refresh_from_db()
        self.assertEqual(aluno.plano_ia_texto, "")


class AtencaoTests(AlunosBase):
    def test_marcar_no_cadastro_exige_motivo_e_guarda_quem_e_quando(self):
        resposta, _ = self.criar(precisa_atencao="on")
        self.assertEqual(resposta.status_code, 200)
        self.assertIn("motivo_atencao", resposta.context["form"].errors)

        _, aluno = self.criar(precisa_atencao="on", motivo_atencao="Voltou de afastamento")
        self.assertTrue(aluno.precisa_atencao)
        self.assertEqual(aluno.motivo_atencao, "Voltou de afastamento")
        self.assertEqual(aluno.atencao_marcada_por, self.coord)
        self.assertIsNotNone(aluno.atencao_marcada_em)

    def test_editar_sem_mudar_a_atencao_mantem_a_data_e_quem_marcou(self):
        _, aluno = self.criar(precisa_atencao="on", motivo_atencao="Voltou de afastamento")
        marcada_em = aluno.atencao_marcada_em
        self.client.force_login(self.nucleo)
        self.client.post(
            reverse("alunos:editar", kwargs={"pk": aluno.pk}),
            self.dados(precisa_atencao="on", motivo_atencao="Voltou de afastamento", observacoes="Nova observação"),
        )
        aluno.refresh_from_db()
        self.assertEqual(aluno.atencao_marcada_em, marcada_em)
        self.assertEqual(aluno.atencao_marcada_por, self.coord)

    def test_acao_rapida_marca_e_desmarca(self):
        aluno = Aluno.objects.create(nome="Lucas", turma=self.turma)
        url = reverse("alunos:atencao", kwargs={"pk": aluno.pk})
        self.client.force_login(self.nucleo)

        self.client.post(url, {"acao": "marcar", "motivo": ""})
        aluno.refresh_from_db()
        self.assertFalse(aluno.precisa_atencao)  # sem motivo não marca

        self.client.post(url, {"acao": "marcar", "motivo": "Faltou muito em outubro"})
        aluno.refresh_from_db()
        self.assertTrue(aluno.precisa_atencao)
        self.assertEqual(aluno.atencao_marcada_por, self.nucleo)

        self.client.post(url, {"acao": "desmarcar"})
        aluno.refresh_from_db()
        self.assertFalse(aluno.precisa_atencao)
        self.assertEqual(aluno.motivo_atencao, "")
        self.assertIsNone(aluno.atencao_marcada_por)

    def test_professor_nao_marca_atencao(self):
        aluno = Aluno.objects.create(nome="Lucas", turma=self.turma)
        aluno.professores.add(self.prof)
        self.client.force_login(self.prof)
        resposta = self.client.post(reverse("alunos:atencao", kwargs={"pk": aluno.pk}), {"acao": "marcar", "motivo": "x"})
        self.assertEqual(resposta.status_code, 403)

    def test_lista_separa_quem_precisa_de_atencao(self):
        Aluno.objects.create(nome="Ana", turma=self.turma, precisa_atencao=True, motivo_atencao="Retomar frações")
        Aluno.objects.create(nome="Bruno", turma=self.turma)
        self.client.force_login(self.coord)
        resposta = self.client.get(reverse("alunos:lista"))
        self.assertEqual([a.nome for a in resposta.context["atencao"]], ["Ana"])
        self.assertEqual([a.nome for a in resposta.context["ativos"]], ["Ana", "Bruno"])
        self.assertContains(resposta, "Retomar frações")


class ListaEArquivoTests(AlunosBase):
    def test_professor_ve_so_os_seus_na_lista(self):
        meu = Aluno.objects.create(nome="Meu aluno", turma=self.turma)
        meu.professores.add(self.prof)
        Aluno.objects.create(nome="De outro", turma=self.turma)
        self.client.force_login(self.prof)
        resposta = self.client.get(reverse("alunos:lista"))
        self.assertEqual([a.nome for a in resposta.context["ativos"]], ["Meu aluno"])
        self.assertContains(resposta, "Meus alunos")
        self.assertNotContains(resposta, "Novo aluno")

    def test_coordenacao_arquiva_e_reativa_sem_apagar(self):
        aluno = Aluno.objects.create(nome="Lucas", turma=self.turma)
        url = reverse("alunos:arquivar", kwargs={"pk": aluno.pk})
        self.client.force_login(self.coord)
        self.client.post(url)
        aluno.refresh_from_db()
        self.assertFalse(aluno.ativo)
        resposta = self.client.get(reverse("alunos:lista"))
        self.assertEqual(resposta.context["ativos"], [])
        self.assertEqual([a.nome for a in resposta.context["arquivados"]], ["Lucas"])

        self.client.post(url)
        aluno.refresh_from_db()
        self.assertTrue(aluno.ativo)

    def test_nucleo_nao_arquiva(self):
        aluno = Aluno.objects.create(nome="Lucas", turma=self.turma)
        self.client.force_login(self.nucleo)
        self.assertEqual(self.client.post(reverse("alunos:arquivar", kwargs={"pk": aluno.pk})).status_code, 403)
