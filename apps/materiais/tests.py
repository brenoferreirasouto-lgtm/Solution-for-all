"""Entrega #7 (Adaptar material) e entrega #8 (material pronto, exportar e listas)."""

import io
import shutil
import tempfile
from unittest import mock

import docx
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from apps.alunos.models import Aluno, Necessidade, TipoAdaptacao
from apps.contas.models import Papel, Usuario
from apps.escola.models import Disciplina, Lecionacao, Turma

from .models import Adaptacao, Material
from .services import ia, texto
from .services.adaptacoes import adaptar

MEDIA_DE_TESTE = tempfile.mkdtemp(prefix="sfa-testes-")


def pdf_com_texto(conteudo=""):
    """Um PDF mínimo e válido, com uma linha de texto (ou nenhuma, como um PDF escaneado)."""
    fluxo = f"BT /F1 12 Tf 72 720 Td ({conteudo}) Tj ET".encode("latin-1") if conteudo else b""
    objetos = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R"
        b" /Resources << /Font << /F1 5 0 R >> >> >>",
        b"<< /Length %d >>\nstream\n" % len(fluxo) + fluxo + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    saida = b"%PDF-1.4\n"
    posicoes = []
    for numero, objeto in enumerate(objetos, start=1):
        posicoes.append(len(saida))
        saida += b"%d 0 obj\n" % numero + objeto + b"\nendobj\n"
    inicio_xref = len(saida)
    saida += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objetos) + 1)
    for posicao in posicoes:
        saida += b"%010d 00000 n \n" % posicao
    saida += b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (len(objetos) + 1, inicio_xref)
    return saida


def docx_com(*paragrafos, tabela=None):
    documento = docx.Document()
    for paragrafo in paragrafos:
        documento.add_paragraph(paragrafo)
    if tabela:
        grade = documento.add_table(rows=len(tabela), cols=len(tabela[0]))
        for i, linha in enumerate(tabela):
            for j, valor in enumerate(linha):
                grade.cell(i, j).text = valor
    saida = io.BytesIO()
    documento.save(saida)
    return saida.getvalue()


def arquivo(nome, conteudo):
    return SimpleUploadedFile(nome, conteudo)


FOTOSSINTESE = (
    "Fotossíntese\n\n"
    "A fotossíntese é o processo pelo qual as plantas produzem o próprio alimento. "
    "Ela acontece nas folhas.\n\n"
    "A planta precisa de água, gás carbônico e luz. No final, ela libera oxigênio."
)


# Extração de texto ------------------------------------------------------------
class ExtracaoTests(TestCase):
    def test_pdf_com_texto(self):
        self.assertIn("As plantas fazem fotossintese", texto.extrair_texto(arquivo("aula.pdf", pdf_com_texto("As plantas fazem fotossintese."))))

    def test_pdf_escaneado_avisa_para_colar_o_texto(self):
        with self.assertRaisesMessage(texto.TextoIlegivel, "parece ser escaneado"):
            texto.extrair_texto(arquivo("foto.pdf", pdf_com_texto()))

    def test_arquivo_que_nao_e_pdf(self):
        with self.assertRaisesMessage(texto.TextoIlegivel, "não é um PDF válido"):
            texto.extrair_texto(arquivo("aula.pdf", b"isto nao e pdf"))

    def test_word_com_paragrafos_e_tabela(self):
        conteudo = docx_com("Sistema solar", "São oito planetas.", tabela=[["Planeta", "Tipo"], ["Júpiter", "Gasoso"]])
        extraido = texto.extrair_texto(arquivo("aula.docx", conteudo))
        self.assertIn("São oito planetas.", extraido)
        self.assertIn("Júpiter | Gasoso", extraido)

    def test_word_invalido(self):
        with self.assertRaisesMessage(texto.TextoIlegivel, "não é um .docx válido"):
            texto.extrair_texto(arquivo("aula.docx", b"oi"))

    def test_txt_em_utf8_e_em_windows(self):
        self.assertEqual(texto.extrair_texto(arquivo("a.txt", "Ação e reação.".encode())), "Ação e reação.")
        self.assertEqual(texto.extrair_texto(arquivo("b.txt", "Ação e reação.".encode("cp1252"))), "Ação e reação.")

    def test_formatos_recusados(self):
        with self.assertRaisesMessage(texto.TextoIlegivel, ".doc antigos"):
            texto.extrair_texto(arquivo("aula.doc", b"x"))
        with self.assertRaisesMessage(texto.TextoIlegivel, "PDF, Word (.docx) ou .txt"):
            texto.extrair_texto(arquivo("foto.png", b"x"))

    def test_arquivo_grande_demais(self):
        with mock.patch.object(texto, "LIMITE_ARQUIVO", 10):
            with self.assertRaisesMessage(texto.TextoIlegivel, "passa de"):
                texto.extrair_texto(arquivo("a.txt", b"texto com mais de dez bytes"))

    def test_titulo_sugerido(self):
        self.assertEqual(texto.titulo_sugerido("vulcoes.pdf", "Vulcões\nUm vulcão é uma abertura."), "Vulcões")
        self.assertEqual(texto.titulo_sugerido("aula_de-ciencias.pdf", "Um texto que começa direto."), "Aula de ciencias")
        self.assertEqual(texto.titulo_sugerido("", "Frações no dia a dia\n\nTexto."), "Frações no dia a dia")
        self.assertEqual(texto.titulo_sugerido("", ""), "Material sem título")


# IA simulada ------------------------------------------------------------------
class IaSimuladaTests(TestCase):
    def gerar(self, slug, conteudo=FOTOSSINTESE):
        return ia.gerar_adaptacao(conteudo, TipoAdaptacao.objects.get(slug=slug))

    def test_cada_formato_organiza_o_texto_de_um_jeito(self):
        simples = self.gerar("simples").conteudo
        self.assertIn("A fotossíntese é o processo pelo qual as plantas produzem o próprio alimento.\nEla acontece nas folhas.", simples)
        self.assertTrue(self.gerar("resumo").conteudo.startswith("Ideias principais\n\n• A fotossíntese"))
        self.assertIn("1. A fotossíntese", self.gerar("visual").conteudo)
        audio = self.gerar("audio").conteudo
        self.assertTrue(audio.startswith("Ouça com atenção.") and audio.endswith("Fim do texto."))
        for slug in ("simples", "resumo", "visual", "audio"):
            with self.subTest(formato=slug):
                resultado = self.gerar(slug)
                self.assertEqual(resultado.gerado_por, "simulada")
                self.assertNotIn("Fotossíntese\n", resultado.conteudo)  # o título fica de fora

    def test_texto_vazio_e_texto_longo(self):
        self.assertIn("não tem texto legível", self.gerar("simples", "").conteudo)
        longo = " ".join(f"Frase número {n}." for n in range(40))
        self.assertIn(ia.AVISO_CORTE, self.gerar("simples", longo).conteudo)


# Base das telas -----------------------------------------------------------------
@override_settings(MEDIA_ROOT=MEDIA_DE_TESTE)
class MateriaisBase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.coord = Usuario.objects.create_user("coord@teste.com", "senha-teste-1", nome="Coord", papel=Papel.COORDENADOR)
        cls.nucleo = Usuario.objects.create_user("nucleo@teste.com", "senha-teste-1", nome="Núcleo", papel=Papel.NUCLEO)
        cls.prof = Usuario.objects.create_user("prof@teste.com", "senha-teste-1", nome="Prof. Ana", papel=Papel.PROFESSOR)
        cls.colega = Usuario.objects.create_user("colega@teste.com", "senha-teste-1", nome="Prof. Caio", papel=Papel.PROFESSOR)
        cls.outro = Usuario.objects.create_user("outro@teste.com", "senha-teste-1", nome="Prof. Beto", papel=Papel.PROFESSOR)
        cls.turma = Turma.objects.create(nome="7º B", ano_letivo=2026)
        cls.ciencias = Disciplina.objects.create(nome="Ciências")
        Lecionacao.objects.create(professor=cls.prof, turma=cls.turma, disciplina=cls.ciencias)

        cls.simples = TipoAdaptacao.objects.get(slug="simples")
        cls.resumo = TipoAdaptacao.objects.get(slug="resumo")
        cls.aluno = Aluno.objects.create(nome="Beatriz Lima", turma=cls.turma)
        cls.aluno.professores.add(cls.prof, cls.colega)
        cls.aluno.necessidades.add(Necessidade.objects.get(slug="tea"))
        cls.aluno.formatos.add(cls.resumo)
        cls.aluno_de_outro = Aluno.objects.create(nome="Davi Rocha", turma=cls.turma)
        cls.aluno_de_outro.professores.add(cls.outro)
        cls.arquivado = Aluno.objects.create(nome="Eva Souza", turma=cls.turma, ativo=False)
        cls.arquivado.professores.add(cls.prof)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(MEDIA_DE_TESTE, ignore_errors=True)

    def setUp(self):
        self.client.force_login(self.prof)

    def enviar(self, **dados):
        base = {"aluno": self.aluno.pk, "origem": "texto", "texto": FOTOSSINTESE, "tipo": self.simples.pk}
        base.update(dados)
        return self.client.post(reverse("materiais:adaptar"), base)

    def material_com_adaptacao(self, professor=None):
        professor = professor or self.prof
        material = Material.objects.create(titulo="Fotossíntese", texto_extraido=FOTOSSINTESE, professor=professor)
        return material, adaptar(material, self.aluno, self.simples, professor)


# Entrega #7: Adaptar ---------------------------------------------------------------
class AdaptarTelaTests(MateriaisBase):
    def test_vem_do_perfil_com_aluno_e_formato_marcados(self):
        resposta = self.client.get(reverse("materiais:adaptar"), {"aluno": self.aluno.pk})
        form = resposta.context["form"]
        self.assertEqual(form.initial["aluno"], self.aluno.pk)
        self.assertEqual(form.initial["tipo"], self.resumo.pk)
        self.assertContains(resposta, f'data-formatos="{self.resumo.pk}"')

    def test_so_aparecem_os_alunos_ativos_do_professor(self):
        resposta = self.client.get(reverse("materiais:adaptar"), {"aluno": self.aluno_de_outro.pk})
        form = resposta.context["form"]
        self.assertEqual(list(form.fields["aluno"].queryset), [self.aluno])
        self.assertNotIn("aluno", form.initial)

    def test_material_ja_enviado_pela_url(self):
        meu, _ = self.material_com_adaptacao()
        alheio = Material.objects.create(titulo="Outro", texto_extraido="x", professor=self.outro)
        form = self.client.get(reverse("materiais:adaptar"), {"material": meu.pk}).context["form"]
        self.assertEqual((form.initial["origem"], form.initial["material"]), ("material", meu.pk))
        form = self.client.get(reverse("materiais:adaptar"), {"material": alheio.pk}).context["form"]
        self.assertNotIn("material", form.initial)

    def test_sem_materiais_nao_oferece_material_ja_enviado(self):
        form = self.client.get(reverse("materiais:adaptar")).context["form"]
        self.assertEqual([valor for valor, _ in form.fields["origem"].choices], ["arquivo", "texto"])

    def test_professor_sem_alunos_ve_o_aviso(self):
        sem_alunos = Usuario.objects.create_user("novo@teste.com", "senha-teste-1", nome="Novo", papel=Papel.PROFESSOR)
        self.client.force_login(sem_alunos)
        self.assertContains(self.client.get(reverse("materiais:adaptar")), "Você ainda não tem alunos vinculados")


class AdaptarEnvioTests(MateriaisBase):
    def test_texto_colado_cria_material_e_adaptacao(self):
        resposta = self.enviar()
        adaptacao = Adaptacao.objects.get()
        self.assertRedirects(resposta, reverse("materiais:adaptacao", kwargs={"pk": adaptacao.pk}))
        material = adaptacao.material
        self.assertEqual(material.titulo, "Fotossíntese")
        self.assertEqual(material.professor, self.prof)
        self.assertEqual(material.disciplina, self.ciencias)  # a matéria do professor na turma do aluno
        self.assertFalse(material.arquivo)
        self.assertEqual(
            (adaptacao.aluno, adaptacao.tipo, adaptacao.versao, adaptacao.status, adaptacao.criado_por),
            (self.aluno, self.simples, 1, Adaptacao.Status.CONCLUIDA, self.prof),
        )
        self.assertIn("Ela acontece nas folhas.", adaptacao.conteudo)

    def test_pdf_e_word(self):
        self.enviar(origem="arquivo", arquivo=arquivo("vulcoes.pdf", pdf_com_texto("Um vulcao e uma abertura na crosta.")))
        material = Material.objects.get()
        self.assertTrue(material.arquivo.name.endswith(".pdf"))
        self.assertIn("Um vulcao e uma abertura", material.texto_extraido)
        self.assertEqual(material.titulo, "Vulcoes")

        self.enviar(origem="arquivo", titulo="Sistema solar", arquivo=arquivo("aula.docx", docx_com("São oito planetas.")))
        material = Material.objects.get(titulo="Sistema solar")
        self.assertEqual(material.texto_extraido, "São oito planetas.")

    def test_pdf_escaneado_volta_com_o_aviso(self):
        resposta = self.enviar(origem="arquivo", arquivo=arquivo("foto.pdf", pdf_com_texto()))
        self.assertEqual(resposta.status_code, 200)
        self.assertIn("parece ser escaneado", resposta.context["form"].errors["arquivo"][0])
        self.assertFalse(Material.objects.exists())

    def test_cada_forma_de_envio_exige_o_seu_campo(self):
        Material.objects.create(titulo="Antigo", texto_extraido="x", professor=self.prof)
        casos = (("arquivo", "arquivo", {}), ("texto", "texto", {"texto": ""}), ("material", "material", {}))
        for origem, campo, extra in casos:
            with self.subTest(origem=origem):
                resposta = self.enviar(origem=origem, **extra)
                self.assertIn(campo, resposta.context["form"].errors)
        self.assertFalse(Adaptacao.objects.exists())

    def test_reaproveita_o_material_e_conta_a_versao(self):
        material, primeira = self.material_com_adaptacao()
        self.enviar(origem="material", material=material.pk)
        self.enviar(origem="material", material=material.pk, tipo=self.resumo.pk)
        self.assertEqual(Material.objects.count(), 1)
        versoes = Adaptacao.objects.filter(tipo=self.simples).values_list("versao", flat=True)
        self.assertEqual(sorted(versoes), [1, 2])
        self.assertEqual(Adaptacao.objects.get(tipo=self.resumo).versao, 1)

    def test_nao_aceita_aluno_nem_material_de_outro_professor(self):
        alheio = Material.objects.create(titulo="Outro", texto_extraido="x", professor=self.outro)
        self.assertIn("aluno", self.enviar(aluno=self.aluno_de_outro.pk).context["form"].errors)
        self.assertIn("aluno", self.enviar(aluno=self.arquivado.pk).context["form"].errors)
        self.assertIn("material", self.enviar(origem="material", material=alheio.pk).context["form"].errors)
        self.assertFalse(Adaptacao.objects.exists())

    def test_ia_recebe_so_o_texto_e_o_formato(self):
        with mock.patch.object(ia, "gerar_adaptacao", wraps=ia.gerar_adaptacao) as chamada:
            self.enviar()
        chamada.assert_called_once()
        args = chamada.call_args.args
        self.assertEqual(args[1], self.simples)
        self.assertEqual(args[0], Material.objects.get().texto_extraido)
        self.assertNotIn("Beatriz", repr(chamada.call_args))

    def test_ia_fora_do_ar_fica_registrada_como_erro(self):
        with mock.patch.object(ia, "gerar_adaptacao", side_effect=ia.IAIndisponivel):
            resposta = self.enviar()
        adaptacao = Adaptacao.objects.get()
        self.assertEqual(adaptacao.status, Adaptacao.Status.ERRO)
        self.assertContains(self.client.get(resposta.url), "A IA não respondeu nesta versão")

    def test_so_professor_adapta(self):
        for usuario in (self.coord, self.nucleo):
            self.client.force_login(usuario)
            self.assertEqual(self.enviar().status_code, 403)
        self.assertFalse(Adaptacao.objects.exists())


# Entrega #8: material pronto ----------------------------------------------------------
class MaterialProntoTests(MateriaisBase):
    def test_autor_revisa_e_os_outros_so_leem(self):
        _, adaptacao = self.material_com_adaptacao()
        url = reverse("materiais:adaptacao", kwargs={"pk": adaptacao.pk})
        resposta = self.client.get(url)
        self.assertContains(resposta, 'name="conteudo"')
        self.assertContains(resposta, "Refazer")
        self.assertContains(resposta, "Gerado por IA (simulada)")
        self.assertContains(resposta, "Ainda não revisado")

        for leitor in (self.colega, self.nucleo, self.coord):  # o colega também acompanha o aluno
            self.client.force_login(leitor)
            resposta = self.client.get(url)
            with self.subTest(leitor=leitor.nome):
                self.assertEqual(resposta.status_code, 200)
                self.assertNotContains(resposta, 'name="conteudo"')
                self.assertNotContains(resposta, "Refazer")
                self.assertContains(resposta, "Ela acontece nas folhas.")

    def test_salvar_grava_a_revisao(self):
        _, adaptacao = self.material_com_adaptacao()
        url = reverse("materiais:adaptacao_salvar", kwargs={"pk": adaptacao.pk})
        self.client.post(url, {"conteudo": "Texto revisado.\r\nCom duas linhas.  "})
        adaptacao.refresh_from_db()
        self.assertEqual(adaptacao.conteudo, "Texto revisado.\nCom duas linhas.")
        self.assertIsNotNone(adaptacao.revisado_em)
        self.assertContains(self.client.get(reverse("materiais:adaptacao", kwargs={"pk": adaptacao.pk})), "Revisado em")

    def test_salvar_vazio_nao_apaga_o_texto(self):
        _, adaptacao = self.material_com_adaptacao()
        resposta = self.client.post(reverse("materiais:adaptacao_salvar", kwargs={"pk": adaptacao.pk}), {"conteudo": "  "})
        self.assertEqual(resposta.status_code, 302)
        adaptacao.refresh_from_db()
        self.assertIn("Ela acontece nas folhas.", adaptacao.conteudo)
        self.assertIsNone(adaptacao.revisado_em)

    def test_so_quem_criou_salva_e_refaz(self):
        _, adaptacao = self.material_com_adaptacao()
        self.client.force_login(self.colega)
        for rota in ("materiais:adaptacao_salvar", "materiais:adaptacao_refazer"):
            with self.subTest(rota=rota):
                resposta = self.client.post(reverse(rota, kwargs={"pk": adaptacao.pk}), {"conteudo": "x"})
                self.assertEqual(resposta.status_code, 404)
        self.assertEqual(Adaptacao.objects.count(), 1)

    def test_refazer_cria_nova_versao_e_guarda_a_anterior(self):
        _, primeira = self.material_com_adaptacao()
        resposta = self.client.post(reverse("materiais:adaptacao_refazer", kwargs={"pk": primeira.pk}))
        nova = Adaptacao.objects.exclude(pk=primeira.pk).get()
        self.assertRedirects(resposta, reverse("materiais:adaptacao", kwargs={"pk": nova.pk}))
        self.assertEqual((nova.versao, nova.aluno, nova.tipo), (2, self.aluno, self.simples))
        tela = self.client.get(resposta.url)
        self.assertEqual(list(tela.context["outras_versoes"]), [primeira])

    def test_exportar_nao_mostra_o_aluno(self):
        _, adaptacao = self.material_com_adaptacao()
        adaptacao.revisado_em = adaptacao.criado_em
        adaptacao.save()
        resposta = self.client.get(reverse("materiais:adaptacao_exportar", kwargs={"pk": adaptacao.pk}))
        self.assertContains(resposta, "Ela acontece nas folhas.")
        self.assertContains(resposta, "IA simulada")
        self.assertContains(resposta, "revisado pelo professor")
        self.assertNotContains(resposta, "Beatriz")
        self.assertNotContains(resposta, "TEA")

    def test_baixar_em_word(self):
        _, adaptacao = self.material_com_adaptacao()
        resposta = self.client.get(reverse("materiais:adaptacao_word", kwargs={"pk": adaptacao.pk}))
        self.assertEqual(resposta["Content-Type"], "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        self.assertEqual(resposta["Content-Disposition"], 'attachment; filename="fotossintese-simples.docx"')
        documento = docx.Document(io.BytesIO(resposta.content))
        textos = "\n".join(p.text for p in documento.paragraphs)
        self.assertIn("Fotossíntese", textos)
        self.assertIn("Ela acontece nas folhas.", textos)
        self.assertNotIn("Beatriz", textos)

    def test_professor_sem_vinculo_nao_ve(self):
        _, adaptacao = self.material_com_adaptacao()
        self.client.force_login(self.outro)
        for rota in ("materiais:adaptacao", "materiais:adaptacao_exportar", "materiais:adaptacao_word"):
            with self.subTest(rota=rota):
                self.assertEqual(self.client.get(reverse(rota, kwargs={"pk": adaptacao.pk})).status_code, 404)


class ListasTests(MateriaisBase):
    def test_professor_ve_so_os_seus_materiais(self):
        meu, _ = self.material_com_adaptacao()
        Material.objects.create(titulo="Material do Beto", texto_extraido="x", professor=self.outro)
        resposta = self.client.get(reverse("materiais:lista"))
        self.assertEqual(list(resposta.context["materiais"]), [meu])
        self.assertEqual(resposta.context["materiais"][0].total_adaptacoes, 1)
        self.assertContains(resposta, "Adaptar material")

    def test_gestao_ve_todos_com_o_professor(self):
        self.material_com_adaptacao()
        Material.objects.create(titulo="Material do Beto", texto_extraido="x", professor=self.outro)
        self.client.force_login(self.nucleo)
        resposta = self.client.get(reverse("materiais:lista"))
        self.assertEqual(len(resposta.context["materiais"]), 2)
        self.assertContains(resposta, "Prof. Beto")
        self.assertNotContains(resposta, 'href="/materiais/adaptar/"')

    def test_detalhe_do_material(self):
        material, adaptacao = self.material_com_adaptacao()
        resposta = self.client.get(reverse("materiais:detalhe", kwargs={"pk": material.pk}))
        self.assertEqual(list(resposta.context["adaptacoes"]), [adaptacao])
        self.assertContains(resposta, "texto colado")
        self.assertContains(resposta, f"?material={material.pk}")  # Adaptar para outro aluno

        self.client.force_login(self.outro)
        self.assertEqual(self.client.get(reverse("materiais:detalhe", kwargs={"pk": material.pk})).status_code, 404)

    def test_perfil_do_aluno_mostra_o_historico(self):
        _, adaptacao = self.material_com_adaptacao()
        resposta = self.client.get(reverse("alunos:detalhe", kwargs={"pk": self.aluno.pk}))
        self.assertContains(resposta, reverse("materiais:adaptacao", kwargs={"pk": adaptacao.pk}))
        self.assertContains(resposta, f"?aluno={self.aluno.pk}")
