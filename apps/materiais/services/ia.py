"""
Serviço de IA do Solution for All.

Hoje a IA é SIMULADA: nenhuma API é chamada e nenhum dado sai do app. A
adaptação reorganiza o próprio texto do material conforme o formato. Quando o
grupo decidir ligar a API gratuita (entrega #2), só este arquivo muda; views,
banco e rotas continuam iguais. Antes de ligar, atualize a Política de
Privacidade (provedor e transferência internacional).

Regra de privacidade (LGPD): `gerar_adaptacao` recebe só o texto do material
e o formato; `gerar_plano_apoio` recebe só os itens de catálogo marcados no
cadastro (necessidades e formatos). Nunca passe o nome do aluno, as
observações nem dados de diagnóstico para a IA.
"""

import re
from dataclasses import dataclass

LIMITE_ENTRADA = 12000  # caracteres do material que vão para a IA
LIMITE_FRASES = 15
AVISO_CORTE = "(O material original continua. Esta prévia simulada usa só o começo do texto.)"


@dataclass(frozen=True)
class ResultadoIA:
    conteudo: str
    gerado_por: str


class IAIndisponivel(RuntimeError):
    """A IA não respondeu (limite do plano gratuito, rede...). A adaptação fica com status Erro."""


def gerar_adaptacao(texto: str, tipo) -> ResultadoIA:
    """
    Adapta `texto` para o formato `tipo` (um TipoAdaptacao do catálogo).

    Recebe só o texto do material e o formato, nunca o aluno. A IA de verdade
    usaria `tipo.instrucao_ia` como pedido. Versão simulada: reorganiza o
    próprio texto conforme o formato (frases curtas, tópicos, passos ou texto
    para ouvir), sem reescrever o conteúdo.
    """
    paragrafos = _paragrafos(texto)
    if not paragrafos:
        return ResultadoIA(conteudo="(O material enviado não tem texto legível.)", gerado_por="simulada")
    montar = _FORMATOS.get(getattr(tipo, "slug", ""), _simples)
    return ResultadoIA(conteudo=montar(paragrafos).strip(), gerado_por="simulada")


def _paragrafos(texto):
    """Lista de parágrafos; cada um é uma lista de frases. Títulos (linha curta sem ponto) ficam de fora."""
    texto = (texto or "")[:LIMITE_ENTRADA]
    blocos = []
    for bloco in re.split(r"\n\s*\n", texto):
        linhas = [linha.strip() for linha in bloco.split("\n") if linha.strip()]
        # Título colado no parágrafo (comum em PDF): sai do começo do bloco.
        while len(linhas) > 1 and _parece_titulo(linhas[0]):
            linhas.pop(0)
        if linhas:
            blocos.append(" ".join(" ".join(linhas).split()))
    # Tira os títulos, a não ser que o texto inteiro seja feito de linhas curtas (ex.: uma lista).
    blocos = [b for b in blocos if not _parece_titulo(b)] or blocos
    return [
        [f.strip() for f in re.split(r"(?<=[.!?…])\s+(?=[A-ZÀ-Ý0-9\"“(•-])", bloco) if f.strip()]
        for bloco in blocos
    ]


def _parece_titulo(bloco):
    return len(bloco.split()) <= 10 and bloco[-1] not in ".!?…:;,"


def _essencial(frase, palavras):
    """Encurta frases longas no primeiro sinal de pausa depois de 5 palavras."""
    if len(frase.split()) <= palavras:
        return frase
    for corte in re.finditer(r"[,;:]", frase):
        inicio = frase[: corte.start()]
        if 5 <= len(inicio.split()) <= palavras:
            return inicio + "."
    return " ".join(frase.split()[:palavras]).rstrip(",;:") + "…"


def _simples(paragrafos):
    """Uma frase por linha; frases com ponto e vírgula viram duas."""
    blocos, total, cortou = [], 0, False
    for frases in paragrafos:
        linhas = []
        for frase in frases:
            for curta in (p.strip() for p in frase.split(";") if p.strip()):
                if total >= LIMITE_FRASES:
                    cortou = True
                    break
                curta = curta[0].upper() + curta[1:]
                linhas.append(curta if curta[-1] in ".!?…" else curta + ".")
                total += 1
        if linhas:
            blocos.append("\n".join(linhas))
        if cortou:
            break
    if cortou:
        blocos.append(AVISO_CORTE)
    return "\n\n".join(blocos)


def _resumo(paragrafos):
    ideias = paragrafos[0][:4] if len(paragrafos) == 1 else [frases[0] for frases in paragrafos[:6]]
    return "Ideias principais\n\n" + "\n".join(f"• {_essencial(i, 22)}" for i in ideias)


def _visual(paragrafos):
    frases = [f for p in paragrafos for f in p][:8]
    passos = [f"{n}. {_essencial(f, 14)}" for n, f in enumerate(frases, start=1)]
    return "Esquema em passos\n\n" + "\n".join(passos)


def _audio(paragrafos):
    frases = [" ".join(re.sub(r"[•|*#_<>\[\]{}]", " ", f).split()) for p in paragrafos for f in p][:12]
    frases = [f for f in frases if f]
    blocos = [" ".join(frases[i : i + 2]) for i in range(0, len(frases), 2)]
    return "\n\n".join(["Ouça com atenção.", *blocos, "Fim do texto."])


_FORMATOS = {"simples": _simples, "resumo": _resumo, "visual": _visual, "audio": _audio}


# Plano com IA do cadastro de aluno (entrega #5) ------------------------------
# Versão simulada: estratégias gerais por necessidade do catálogo. A IA de
# verdade receberia os mesmos dados (nomes do catálogo), nunca o aluno.
ESTRATEGIAS_POR_NECESSIDADE = {
    "tea": (
        "Antecipe a rotina da aula e avise com antecedência quando algo mudar.",
        "Dê uma instrução por vez, de forma direta, com apoio visual.",
        "Combine um sinal ou um espaço para pausa quando houver sobrecarga.",
    ),
    "tdah": (
        "Divida as atividades em etapas curtas, com pausas planejadas.",
        "Mostre o objetivo da tarefa no início e confira o andamento em pontos combinados.",
        "Reduza as distrações por perto e alterne tarefas paradas com tarefas com movimento.",
    ),
    "dislexia": (
        "Use fonte maior, espaçamento amplo e parágrafos curtos.",
        "Ofereça o conteúdo também em áudio e leia os enunciados em voz alta.",
        "Avalie a compreensão também de forma oral, sem penalizar a ortografia.",
    ),
    "deficiencia-visual": (
        "Prefira alto contraste e descreva imagens, gráficos e esquemas.",
        "Entregue arquivos que funcionem com leitor de tela e ampliação.",
    ),
    "deficiencia-auditiva": (
        "Acompanhe as explicações orais com texto escrito ou legenda.",
        "Fale de frente para a turma e use apoio visual nas instruções.",
    ),
    "deficiencia-motora": (
        "Dê mais tempo para atividades escritas e aceite resposta oral ou digital.",
        "Organize o material para exigir pouca manipulação.",
    ),
}


def gerar_plano_apoio(necessidades, formatos) -> ResultadoIA:
    """
    Sugere estratégias de apoio para o "Plano com IA" do cadastro de aluno.

    Recebe só itens de catálogo (Necessidade e TipoAdaptacao), nunca o aluno.
    Versão simulada: junta estratégias gerais de cada necessidade marcada.
    """
    partes = ["Sugestões de apoio (IA simulada)"]
    for necessidade in necessidades:
        estrategias = ESTRATEGIAS_POR_NECESSIDADE.get(necessidade.slug) or (
            "Combine com o núcleo psicopedagógico as estratégias de apoio mais adequadas.",
        )
        partes.append("\n".join([necessidade.nome, *(f"• {e}" for e in estrategias)]))
    if formatos:
        linhas = [
            f"• {f.nome}: {f.descricao}" if f.descricao else f"• {f.nome}" for f in formatos
        ]
        partes.append("\n".join(["Formatos recomendados para os materiais", *linhas]))
    if len(partes) == 1:
        partes.append("Marque ao menos uma necessidade ou um formato para a IA sugerir estratégias.")
    partes.append("Revise estas sugestões com o núcleo psicopedagógico antes de usar.")
    return ResultadoIA(conteudo="\n\n".join(partes), gerado_por="simulada")
