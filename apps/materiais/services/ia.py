"""
Serviço de IA do Solution for All, versão em Python básico.

Hoje a IA é SIMULADA: nenhuma API é chamada e nenhum dado sai do app. A
adaptação reorganiza o próprio texto do material conforme o formato. Quando o
grupo decidir ligar a API gratuita (entrega #2), só este arquivo muda; views,
banco e rotas continuam iguais.

Regra de privacidade (LGPD): `gerar_adaptacao` recebe só o texto do material
e o formato; `gerar_plano_apoio` recebe só os itens de catálogo marcados no
cadastro (necessidades e formatos). Nunca passe o nome do aluno, as
observações nem dados de diagnóstico para a IA.

Usa só: strings, listas, for/while, if e funções.
"""

LIMITE_ENTRADA = 12000  # caracteres do material que vão para a IA
LIMITE_FRASES = 15
AVISO_CORTE = "(O material original continua. Esta prévia simulada usa só o começo do texto.)"

# Letras que, depois de um ponto final e um espaço, indicam que começa outra frase.
FIM_DE_FRASE = ".!?…"
INICIO_DE_FRASE = "ABCDEFGHIJKLMNOPQRSTUVWXYZÀÁÂÃÄÅÆÇÈÉÊËÌÍÎÏÐÑÒÓÔÕÖ×ØÙÚÛÜÝ0123456789\"“(•-"
# Símbolos que atrapalham a leitura em voz alta.
SIMBOLOS_DO_AUDIO = "•|*#_<>[]{}"


# As duas classes abaixo existem por obrigação: o resto do projeto (Django e
# testes) lê `resultado.conteudo` e `resultado.gerado_por`, e o Python só deixa
# dar `raise` em exceções, que são classes. Nenhuma tem método.
class ResultadoIA:
    """Guarda o texto gerado (conteudo) e quem gerou (gerado_por)."""

    conteudo = ""
    gerado_por = ""


class IAIndisponivel(RuntimeError):
    """A IA não respondeu (limite do plano gratuito, rede...). A adaptação fica com status Erro."""


def novo_resultado(conteudo, gerado_por):
    resultado = ResultadoIA()
    resultado.conteudo = conteudo
    resultado.gerado_por = gerado_por
    return resultado


def gerar_adaptacao(texto, tipo):
    """
    Adapta `texto` para o formato `tipo` (um TipoAdaptacao do catálogo).

    Recebe só o texto do material e o formato, nunca o aluno. A IA de verdade
    usaria `tipo.instrucao_ia` como pedido. Versão simulada: reorganiza o
    próprio texto conforme o formato (frases curtas, tópicos, passos ou texto
    para ouvir), sem reescrever o conteúdo.
    """
    paragrafos = _paragrafos(texto)
    if len(paragrafos) == 0:
        return novo_resultado("(O material enviado não tem texto legível.)", "simulada")

    slug = getattr(tipo, "slug", "")
    if slug == "resumo":
        conteudo = _resumo(paragrafos)
    elif slug == "visual":
        conteudo = _visual(paragrafos)
    elif slug == "audio":
        conteudo = _audio(paragrafos)
    else:
        conteudo = _simples(paragrafos)
    return novo_resultado(conteudo.strip(), "simulada")


# ---------------------------------------------------------------------------
# Quebrar o texto em parágrafos e frases
# ---------------------------------------------------------------------------
def _blocos_de_linhas(texto):
    """Separa o texto nas linhas em branco. Cada bloco é uma lista de linhas sem espaços nas pontas."""
    blocos = []
    atual = []
    for linha in texto.split("\n"):
        linha = linha.strip()
        if linha == "":
            # Linha em branco: termina o bloco que estava sendo montado.
            if len(atual) > 0:
                blocos.append(atual)
            atual = []
        else:
            atual.append(linha)
    if len(atual) > 0:
        blocos.append(atual)
    return blocos


def _dividir_em_frases(bloco):
    """Corta o bloco onde há ponto/!/?/… + espaço + começo de outra frase."""
    frases = []
    comeco = 0
    for i in range(1, len(bloco) - 1):
        if bloco[i] == " " and bloco[i - 1] in FIM_DE_FRASE and bloco[i + 1] in INICIO_DE_FRASE:
            frases.append(bloco[comeco:i])
            comeco = i + 1
    frases.append(bloco[comeco:])

    limpas = []
    for frase in frases:
        frase = frase.strip()
        if frase != "":
            limpas.append(frase)
    return limpas


def _paragrafos(texto):
    """Lista de parágrafos; cada um é uma lista de frases. Títulos (linha curta sem ponto) ficam de fora."""
    if texto is None:
        texto = ""
    texto = texto[:LIMITE_ENTRADA]

    blocos = []
    for linhas in _blocos_de_linhas(texto):
        # Título colado no parágrafo (comum em PDF): sai do começo do bloco.
        while len(linhas) > 1 and _parece_titulo(linhas[0]):
            linhas.pop(0)
        blocos.append(" ".join(" ".join(linhas).split()))

    # Tira os títulos, a não ser que o texto inteiro seja feito de linhas curtas (ex.: uma lista).
    sem_titulos = []
    for bloco in blocos:
        if not _parece_titulo(bloco):
            sem_titulos.append(bloco)
    if len(sem_titulos) > 0:
        blocos = sem_titulos

    paragrafos = []
    for bloco in blocos:
        paragrafos.append(_dividir_em_frases(bloco))
    return paragrafos


def _parece_titulo(bloco):
    return len(bloco.split()) <= 10 and bloco[-1] not in ".!?…:;,"


def _essencial(frase, palavras):
    """Encurta frases longas no primeiro sinal de pausa depois de 5 palavras."""
    if len(frase.split()) <= palavras:
        return frase
    for i in range(len(frase)):
        if frase[i] in ",;:":
            inicio = frase[:i]
            if 5 <= len(inicio.split()) <= palavras:
                return inicio + "."
    return " ".join(frase.split()[:palavras]).rstrip(",;:") + "…"


# ---------------------------------------------------------------------------
# Os quatro formatos
# ---------------------------------------------------------------------------
def _simples(paragrafos):
    """Uma frase por linha; frases com ponto e vírgula viram duas."""
    blocos = []
    total = 0
    cortou = False
    for frases in paragrafos:
        linhas = []
        for frase in frases:
            for pedaco in frase.split(";"):
                curta = pedaco.strip()
                if curta == "":
                    continue
                if total >= LIMITE_FRASES:
                    cortou = True
                    break
                curta = curta[0].upper() + curta[1:]
                if curta[-1] in ".!?…":
                    linhas.append(curta)
                else:
                    linhas.append(curta + ".")
                total = total + 1
        if len(linhas) > 0:
            blocos.append("\n".join(linhas))
        if cortou:
            break
    if cortou:
        blocos.append(AVISO_CORTE)
    return "\n\n".join(blocos)


def _resumo(paragrafos):
    if len(paragrafos) == 1:
        ideias = paragrafos[0][:4]
    else:
        ideias = []
        for frases in paragrafos[:6]:
            ideias.append(frases[0])

    linhas = []
    for ideia in ideias:
        linhas.append("• " + _essencial(ideia, 22))
    return "Ideias principais\n\n" + "\n".join(linhas)


def _visual(paragrafos):
    todas = []
    for paragrafo in paragrafos:
        for frase in paragrafo:
            todas.append(frase)
    frases = todas[:8]

    passos = []
    for i in range(len(frases)):
        passos.append(f"{i + 1}. {_essencial(frases[i], 14)}")
    return "Esquema em passos\n\n" + "\n".join(passos)


def _audio(paragrafos):
    todas = []
    for paragrafo in paragrafos:
        for frase in paragrafo:
            for simbolo in SIMBOLOS_DO_AUDIO:
                frase = frase.replace(simbolo, " ")
            todas.append(" ".join(frase.split()))

    frases = []
    for frase in todas[:12]:
        if frase != "":
            frases.append(frase)

    partes = ["Ouça com atenção."]
    for i in range(0, len(frases), 2):
        partes.append(" ".join(frases[i : i + 2]))  # duas frases por bloco
    partes.append("Fim do texto.")
    return "\n\n".join(partes)


# ---------------------------------------------------------------------------
# Plano com IA do cadastro de aluno (entrega #5)
# ---------------------------------------------------------------------------
def estrategias_da_necessidade(slug):
    """Estratégias gerais de uma necessidade do catálogo (lista vazia se não conhecemos)."""
    if slug == "tea":
        return [
            "Antecipe a rotina da aula e avise com antecedência quando algo mudar.",
            "Dê uma instrução por vez, de forma direta, com apoio visual.",
            "Combine um sinal ou um espaço para pausa quando houver sobrecarga.",
        ]
    if slug == "tdah":
        return [
            "Divida as atividades em etapas curtas, com pausas planejadas.",
            "Mostre o objetivo da tarefa no início e confira o andamento em pontos combinados.",
            "Reduza as distrações por perto e alterne tarefas paradas com tarefas com movimento.",
        ]
    if slug == "dislexia":
        return [
            "Use fonte maior, espaçamento amplo e parágrafos curtos.",
            "Ofereça o conteúdo também em áudio e leia os enunciados em voz alta.",
            "Avalie a compreensão também de forma oral, sem penalizar a ortografia.",
        ]
    if slug == "deficiencia-visual":
        return [
            "Prefira alto contraste e descreva imagens, gráficos e esquemas.",
            "Entregue arquivos que funcionem com leitor de tela e ampliação.",
        ]
    if slug == "deficiencia-auditiva":
        return [
            "Acompanhe as explicações orais com texto escrito ou legenda.",
            "Fale de frente para a turma e use apoio visual nas instruções.",
        ]
    if slug == "deficiencia-motora":
        return [
            "Dê mais tempo para atividades escritas e aceite resposta oral ou digital.",
            "Organize o material para exigir pouca manipulação.",
        ]
    return []


def gerar_plano_apoio(necessidades, formatos):
    """
    Sugere estratégias de apoio para o "Plano com IA" do cadastro de aluno.

    Recebe só itens de catálogo (Necessidade e TipoAdaptacao), nunca o aluno.
    Versão simulada: junta estratégias gerais de cada necessidade marcada.
    """
    partes = ["Sugestões de apoio (IA simulada)"]

    for necessidade in necessidades:
        estrategias = estrategias_da_necessidade(necessidade.slug)
        if len(estrategias) == 0:
            estrategias = ["Combine com o núcleo psicopedagógico as estratégias de apoio mais adequadas."]
        linhas = [necessidade.nome]
        for estrategia in estrategias:
            linhas.append("• " + estrategia)
        partes.append("\n".join(linhas))

    if formatos:
        linhas = ["Formatos recomendados para os materiais"]
        for formato in formatos:
            if formato.descricao:
                linhas.append(f"• {formato.nome}: {formato.descricao}")
            else:
                linhas.append(f"• {formato.nome}")
        partes.append("\n".join(linhas))

    if len(partes) == 1:
        partes.append("Marque ao menos uma necessidade ou um formato para a IA sugerir estratégias.")
    partes.append("Revise estas sugestões com o núcleo psicopedagógico antes de usar.")
    return novo_resultado("\n\n".join(partes), "simulada")
