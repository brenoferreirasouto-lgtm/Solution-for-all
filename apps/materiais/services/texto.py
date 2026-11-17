"""
Extrai o texto do material enviado na tela Adaptar (entrega #7).

Aceita PDF com texto, Word (.docx) e .txt. O arquivo nunca é executado nem
aberto por outro programa: só lemos o texto. PDF escaneado (só imagem) não
tem texto para ler; nesse caso o professor recebe um aviso para colar o texto.
"""

import re
import zipfile
from pathlib import Path

LIMITE_ARQUIVO_MB = 10
LIMITE_ARQUIVO = LIMITE_ARQUIVO_MB * 1024 * 1024
EXTENSOES = (".pdf", ".docx", ".txt")
ACEITA = ",".join(EXTENSOES)  # para o atributo accept do <input type="file">


class TextoIlegivel(ValueError):
    """O arquivo não pôde ser lido ou não tem texto. A mensagem vai para a tela."""


def normalizar(texto):
    """Junta espaços repetidos e tira linhas em branco a mais, mantendo os parágrafos."""
    linhas = [" ".join(linha.split()) for linha in (texto or "").replace("\r", "\n").split("\n")]
    texto = "\n".join(linhas)
    return re.sub(r"\n{3,}", "\n\n", texto).strip()


def extrair_texto(arquivo):
    """Devolve o texto de um arquivo enviado (UploadedFile). Levanta TextoIlegivel."""
    extensao = Path(arquivo.name or "").suffix.lower()
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
    finally:
        arquivo.seek(0)

    texto = normalizar(texto)
    if not texto:
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

    if arquivo.read(5) != b"%PDF-":
        raise TextoIlegivel("Este arquivo não é um PDF válido.")
    arquivo.seek(0)
    try:
        leitor = PdfReader(arquivo)
        if leitor.is_encrypted and not leitor.decrypt(""):
            raise TextoIlegivel("Este PDF tem senha. Envie uma cópia sem senha ou cole o texto.")
        return "\n\n".join(pagina.extract_text() or "" for pagina in leitor.pages)
    except TextoIlegivel:
        raise
    except (PdfReadError, ValueError, KeyError, TypeError) as erro:
        raise TextoIlegivel("Não conseguimos ler este PDF. Tente salvar de novo como PDF ou cole o texto.") from erro


def _texto_do_docx(arquivo):
    import docx
    from docx.opc.exceptions import PackageNotFoundError

    if not zipfile.is_zipfile(arquivo):
        raise TextoIlegivel("Este arquivo não é um .docx válido.")
    arquivo.seek(0)
    try:
        documento = docx.Document(arquivo)
    except (PackageNotFoundError, KeyError, ValueError, zipfile.BadZipFile) as erro:
        raise TextoIlegivel("Não conseguimos ler este arquivo do Word. Salve de novo como .docx ou cole o texto.") from erro

    partes = [p.text for p in documento.paragraphs]
    for tabela in documento.tables:
        for linha in tabela.rows:
            partes.append(" | ".join(celula.text.strip() for celula in linha.cells if celula.text.strip()))
    return "\n".join(partes)


def _texto_do_txt(arquivo):
    dados = arquivo.read()
    for codificacao in ("utf-8-sig", "cp1252"):
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
    primeira = next((linha.strip() for linha in (texto or "").splitlines() if linha.strip()), "")
    if primeira and len(primeira.split()) <= 10 and primeira[-1] not in ".!?…:;,":
        titulo = primeira
    elif nome_arquivo:
        titulo = Path(nome_arquivo).stem.replace("_", " ").replace("-", " ")
    else:
        titulo = primeira
    titulo = " ".join(titulo.split())
    if len(titulo) > 80:
        titulo = titulo[:79].rstrip() + "…"
    return (titulo[:1].upper() + titulo[1:]) or "Material sem título"
