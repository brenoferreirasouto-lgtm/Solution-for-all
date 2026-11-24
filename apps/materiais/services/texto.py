"""
Extrai o texto do material enviado na tela Adaptar (entrega #7), versão em Python básico.

Aceita PDF com texto, Word (.docx) e .txt. O arquivo nunca é executado nem
aberto por outro programa: só lemos o texto. PDF escaneado (só imagem) não
tem texto para ler; nesse caso o professor recebe um aviso para colar o texto.

Usa: funções, if/for, try/except, strings e listas. Só os PDFs e os arquivos
Word precisam das bibliotecas pypdf e python-docx (não existe jeito simples de
ler esses formatos sem elas).
"""

import zipfile

LIMITE_ARQUIVO_MB = 10
LIMITE_ARQUIVO = LIMITE_ARQUIVO_MB * 1024 * 1024
EXTENSOES = [".pdf", ".docx", ".txt"]
ACEITA = ",".join(EXTENSOES)  # para o atributo accept do <input type="file">


class TextoIlegivel(ValueError):
    """O arquivo não pôde ser lido ou não tem texto. A mensagem vai para a tela.

    É uma classe porque o Python só deixa dar `raise` em exceções (que são classes).
    """


def normalizar(texto):
    """Junta espaços repetidos e tira linhas em branco a mais, mantendo os parágrafos."""
    if texto is None:
        texto = ""
    texto = texto.replace("\r", "\n")
    linhas_limpas = []
    for linha in texto.split("\n"):
        linhas_limpas.append(" ".join(linha.split()))
    texto = "\n".join(linhas_limpas)
    # Três quebras seguidas (ou mais) viram duas: no máximo uma linha em branco.
    while "\n\n\n" in texto:
        texto = texto.replace("\n\n\n", "\n\n")
    return texto.strip()


def pegar_extensao(nome):
    """Devolve a extensão do nome em minúsculas, como '.pdf' (ou '' se não tiver)."""
    if nome is None:
        nome = ""
    nome = nome.split("/")[-1]
    posicao = nome.rfind(".")
    # posicao 0 é arquivo oculto (".txt") e posição no fim é "nome." - nos dois casos não há extensão.
    if posicao <= 0 or posicao == len(nome) - 1:
        return ""
    return nome[posicao:].lower()


def extrair_texto(arquivo):
    """Devolve o texto de um arquivo enviado (UploadedFile). Levanta TextoIlegivel."""
    extensao = pegar_extensao(arquivo.name)
    if extensao == ".doc":
        raise TextoIlegivel("Arquivos .doc antigos não são aceitos. No Word, use Salvar como > .docx ou PDF.")
    if extensao not in EXTENSOES:
        raise TextoIlegivel("Envie um arquivo PDF, Word (.docx) ou .txt.")
    if arquivo.size > LIMITE_ARQUIVO:
        raise TextoIlegivel(f"O arquivo passa de {LIMITE_ARQUIVO_MB} MB. Envie um arquivo menor ou cole o texto.")

    arquivo.seek(0)
    try:
        if extensao == ".pdf":
            texto = _texto_do_pdf(arquivo)
        elif extensao == ".docx":
            texto = _texto_do_docx(arquivo)
        else:
            texto = _texto_do_txt(arquivo)
    except TextoIlegivel:
        # Volta o arquivo para o começo e deixa o erro seguir para a tela.
        arquivo.seek(0)
        raise
    arquivo.seek(0)

    texto = normalizar(texto)
    if texto == "":
        if extensao == ".pdf":
            raise TextoIlegivel(
                "Não encontramos texto neste PDF. Ele parece ser escaneado (uma imagem). "
                "Envie um PDF com texto ou cole o texto."
            )
        raise TextoIlegivel("O arquivo está vazio. Envie outro arquivo ou cole o texto.")
    return texto


def _texto_do_pdf(arquivo):
    from pypdf import PdfReader
    from pypdf.errors import PdfReadError

    aviso = "Não conseguimos ler este PDF. Tente salvar de novo como PDF ou cole o texto."

    if arquivo.read(5) != b"%PDF-":
        raise TextoIlegivel("Este arquivo não é um PDF válido.")
    arquivo.seek(0)
    try:
        leitor = PdfReader(arquivo)
        if leitor.is_encrypted and not leitor.decrypt(""):
            raise TextoIlegivel("Este PDF tem senha. Envie uma cópia sem senha ou cole o texto.")
        paginas = []
        for pagina in leitor.pages:
            paginas.append(pagina.extract_text() or "")
        return "\n\n".join(paginas)
    except TextoIlegivel:
        # Já é um erro nosso (com mensagem pronta): só deixa passar.
        raise
    except PdfReadError as erro:
        raise TextoIlegivel(aviso) from erro
    except ValueError as erro:
        raise TextoIlegivel(aviso) from erro
    except KeyError as erro:
        raise TextoIlegivel(aviso) from erro
    except TypeError as erro:
        raise TextoIlegivel(aviso) from erro


def _texto_do_docx(arquivo):
    import docx
    from docx.opc.exceptions import PackageNotFoundError

    aviso = "Não conseguimos ler este arquivo do Word. Salve de novo como .docx ou cole o texto."

    if not zipfile.is_zipfile(arquivo):
        raise TextoIlegivel("Este arquivo não é um .docx válido.")
    arquivo.seek(0)
    try:
        documento = docx.Document(arquivo)
    except PackageNotFoundError as erro:
        raise TextoIlegivel(aviso) from erro
    except KeyError as erro:
        raise TextoIlegivel(aviso) from erro
    except ValueError as erro:
        raise TextoIlegivel(aviso) from erro
    except zipfile.BadZipFile as erro:
        raise TextoIlegivel(aviso) from erro

    partes = []
    for paragrafo in documento.paragraphs:
        partes.append(paragrafo.text)
    for tabela in documento.tables:
        for linha in tabela.rows:
            celulas = []
            for celula in linha.cells:
                if celula.text.strip() != "":
                    celulas.append(celula.text.strip())
            partes.append(" | ".join(celulas))
    return "\n".join(partes)


def _texto_do_txt(arquivo):
    dados = arquivo.read()
    # Tenta UTF-8 primeiro; se não der, tenta o formato antigo do Windows.
    for codificacao in ["utf-8-sig", "cp1252"]:
        try:
            return dados.decode(codificacao)
        except UnicodeDecodeError:
            continue
    raise TextoIlegivel("Não conseguimos ler este arquivo de texto. Salve como UTF-8 ou cole o texto.")


def titulo_sugerido(nome_arquivo="", texto=""):
    """
    Título do material quando o professor não digita um: a primeira linha do
    texto, se parecer um título (curta e sem ponto final); senão, o nome do arquivo.
    """
    if texto is None:
        texto = ""
    primeira = ""
    for linha in texto.splitlines():
        if linha.strip() != "":
            primeira = linha.strip()
            break

    if primeira != "" and len(primeira.split()) <= 10 and primeira[-1] not in ".!?…:;,":
        titulo = primeira
    elif nome_arquivo:
        nome = nome_arquivo.split("/")[-1]
        extensao = pegar_extensao(nome)
        nome = nome[: len(nome) - len(extensao)]  # tira a extensão (se não tiver, não tira nada)
        titulo = nome.replace("_", " ").replace("-", " ")
    else:
        titulo = primeira

    titulo = " ".join(titulo.split())
    if len(titulo) > 80:
        titulo = titulo[:79].rstrip() + "…"
    titulo = titulo[:1].upper() + titulo[1:]
    if titulo == "":
        return "Material sem título"
    return titulo
