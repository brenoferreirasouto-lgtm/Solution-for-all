"""Entregas #9 (painel do professor) e #12 (painel da coordenação)."""

from datetime import date
from unittest import mock

from django.urls import reverse

from apps.alunos.models import Aluno
from apps.contas.models import Papel
from apps.core.tests import EsqueletoTestCase

C, P, N = Papel.COORDENADOR, Papel.PROFESSOR, Papel.NUCLEO

# O horário de teste (EsqueletoTestCase) é de segunda-feira. 16/11/2026 é uma segunda.
SEGUNDA = date(2026, 11, 16)
DOMINGO = date(2026, 11, 22)


def hoje_e(dia):
    """Congela o "hoje" usado pelo card de aulas, para o teste não depender do dia em que roda."""
    return mock.patch("apps.escola.models.timezone.localdate", return_value=dia)


class PainelProfessorTests(EsqueletoTestCase):
    def abrir(self, usuario=None, dia=SEGUNDA):
        self.client.force_login(usuario or self.professor)
        with hoje_e(dia):
            return self.client.get(reverse("painel:painel"))

    def test_usa_a_tela_do_professor_com_saudacao(self):
        resposta = self.abrir()
        self.assertEqual(resposta.status_code, 200)
        self.assertTemplateUsed(resposta, "painel/professor.html")
        self.assertContains(resposta, "Painel do professor")
        self.assertContains(resposta, "Prof. Ana")
        self.assertNotContains(resposta, "Em construção")

    def test_resumo_conta_so_os_alunos_do_professor(self):
        resposta = self.abrir()
        valores = {i["rotulo"]: i["valor"] for i in resposta.context["resumo"]}
        self.assertEqual(valores["Meus alunos"], 1)
        self.assertEqual(valores["Materiais enviados"], 1)

    def test_aluno_arquivado_nao_conta(self):
        self.aluno.ativo = False
        self.aluno.save()
        resposta = self.abrir()
        valores = {i["rotulo"]: i["valor"] for i in resposta.context["resumo"]}
        self.assertEqual(valores["Meus alunos"], 0)
        self.assertContains(resposta, "Nenhum aluno vinculado a você ainda")

    def test_aulas_de_hoje_sao_so_do_professor_e_do_dia(self):
        resposta = self.abrir(dia=SEGUNDA)
        self.assertEqual(list(resposta.context["aulas_hoje"]), [self.horario])
        self.assertContains(resposta, "08:00 – 08:50")
        self.assertContains(resposta, "Ciências")

        resposta = self.abrir(self.outro_professor, dia=SEGUNDA)
        self.assertEqual(list(resposta.context["aulas_hoje"]), [])
        self.assertContains(resposta, "Sem aulas hoje.")

        resposta = self.abrir(dia=DOMINGO)
        self.assertEqual(list(resposta.context["aulas_hoje"]), [])

    def test_adaptacao_rapida_leva_o_aluno_para_a_tela_de_adaptar(self):
        resposta = self.abrir()
        self.assertContains(resposta, f'href="{reverse("materiais:adaptar")}?aluno={self.aluno.pk}"')
        self.assertNotContains(resposta, f"?aluno={self.aluno_de_outro.pk}")

    def test_alertas_mostram_so_alunos_do_professor(self):
        self.aluno.marcar_atencao("Faltou duas semanas.", self.coordenador)
        self.aluno.save()
        self.aluno_de_outro.marcar_atencao("Notas caíram.", self.coordenador)
        self.aluno_de_outro.save()
        resposta = self.abrir()
        self.assertEqual(resposta.context["alunos_atencao"], [self.aluno])
        self.assertContains(resposta, "Faltou duas semanas.")
        self.assertNotContains(resposta, "Lucas Martins")
        self.assertNotContains(resposta, "Notas caíram.")

    def test_sem_alertas_mostra_mensagem(self):
        self.assertContains(self.abrir(), "Nenhum dos seus alunos está marcado")

    def test_limite_da_adaptacao_rapida(self):
        for i in range(8):
            outro = Aluno.objects.create(nome=f"Aluno {i}", turma=self.aluno.turma)
            outro.professores.add(self.professor)
        resposta = self.abrir()
        self.assertEqual(len(resposta.context["alunos_rapidos"]), 6)
        self.assertTrue(resposta.context["tem_mais_alunos"])
        self.assertContains(resposta, "Ver todos os alunos")


class PainelCoordenacaoTests(EsqueletoTestCase):
    def abrir(self, dia=SEGUNDA):
        self.client.force_login(self.coordenador)
        with hoje_e(dia):
            return self.client.get(reverse("painel:painel"))

    def numeros(self, resposta):
        return {i["rotulo"]: i["valor"] for i in resposta.context["resumo"]}

    def test_usa_a_tela_da_coordenacao(self):
        resposta = self.abrir()
        self.assertEqual(resposta.status_code, 200)
        self.assertTemplateUsed(resposta, "painel/coordenacao.html")
        self.assertContains(resposta, "Painel da coordenação")
        self.assertNotContains(resposta, "Em construção")

    def test_numeros_da_escola(self):
        numeros = self.numeros(self.abrir())
        # prof, outro_professor e membro_alvo; um membro do núcleo; os 2 alunos do teste.
        self.assertEqual(numeros["Professores"], 3)
        self.assertEqual(numeros["Núcleo psicopedagógico"], 1)
        self.assertEqual(numeros["Alunos ativos"], 2)
        self.assertEqual(numeros["Precisam de atenção"], 0)

    def test_acesso_desativado_e_aluno_arquivado_nao_contam(self):
        self.membro_alvo.is_active = False
        self.membro_alvo.save()
        self.aluno.ativo = False
        self.aluno.save()
        numeros = self.numeros(self.abrir())
        self.assertEqual(numeros["Professores"], 2)
        self.assertEqual(numeros["Alunos ativos"], 1)

    def test_conta_alunos_que_precisam_de_atencao(self):
        self.aluno.marcar_atencao("Faltou.", self.coordenador)
        self.aluno.save()
        self.assertEqual(self.numeros(self.abrir())["Precisam de atenção"], 1)

    def test_aulas_de_hoje_mostram_o_professor(self):
        resposta = self.abrir(dia=SEGUNDA)
        self.assertEqual(list(resposta.context["aulas_hoje"]), [self.horario])
        self.assertContains(resposta, "Prof. Ana")
        self.assertContains(self.abrir(dia=DOMINGO), "Sem aulas hoje.")

    def test_atalhos_usam_as_rotas_do_projeto(self):
        resposta = self.abrir()
        for rota in (
            "alunos:novo",
            "escola:professor_novo",
            "escola:nucleo_novo",
            "escola:horario_novo",
            "escola:equipe",
            "escola:horarios",
            "admin:index",
        ):
            with self.subTest(rota=rota):
                self.assertContains(resposta, f'href="{reverse(rota)}"')

    def test_alunos_por_necessidade_so_conta_ativos(self):
        from apps.alunos.models import Necessidade

        tea = Necessidade.objects.get(slug="tea")  # criada pela migration de catálogos
        self.aluno.necessidades.add(tea)
        self.aluno_de_outro.necessidades.add(tea)
        self.aluno_de_outro.ativo = False
        self.aluno_de_outro.save()
        resposta = self.abrir()
        totais = {n.slug: n.total for n in resposta.context["necessidades"]}
        self.assertEqual(totais["tea"], 1)
        self.assertContains(resposta, f'{reverse("alunos:lista")}?necessidade=tea')


class PainelNucleoTests(EsqueletoTestCase):
    def test_nucleo_continua_na_pagina_em_construcao(self):
        self.client.force_login(self.nucleo)
        resposta = self.client.get(reverse("painel:painel"))
        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, "Painel do núcleo")
        self.assertContains(resposta, "Em construção")
