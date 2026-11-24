# Solution for All - backend simples (só Python básico)
#
# Regras usadas aqui: if/elif/else, for/while, listas e matrizes,
# funções, try/except, strings e arquivos .txt.
# NÃO usa: class, dicionário, set, tupla, list comprehension, lambda.
#
# Como os dados são guardados: cada .txt é uma TABELA.
# Cada linha do arquivo é um registro e os campos ficam separados por ";".
# Na memória, cada tabela vira uma MATRIZ (lista de listas de textos).
#
# Só dados FICTÍCIOS (LGPD). As senhas abaixo existem só para demonstração.
#
# Para rodar:  python solution_for_all.py

import time
import random

# ---------------------------------------------------------------------------
# Nomes dos arquivos
# ---------------------------------------------------------------------------
ARQ_USUARIOS = "usuarios.txt"
ARQ_ALUNOS = "alunos.txt"
ARQ_HORARIOS = "horarios.txt"
ARQ_ADAPTACOES = "adaptacoes.txt"

# ---------------------------------------------------------------------------
# Posição de cada campo (coluna) dentro de uma linha da matriz
# ---------------------------------------------------------------------------
# usuarios.txt  ->  nome;email;senha;papel;aceitou_termos
U_NOME = 0
U_EMAIL = 1
U_SENHA = 2
U_PAPEL = 3
U_ACEITOU = 4
U_COLUNAS = 5

# alunos.txt  ->  nome;turma;necessidades;formatos;como_aprende;dificuldades;
#                 professor_email;atencao;motivo;ativo
A_NOME = 0
A_TURMA = 1
A_NECESSIDADES = 2
A_FORMATOS = 3
A_APRENDE = 4
A_DIFICULDADES = 5
A_PROFESSOR = 6
A_ATENCAO = 7
A_MOTIVO = 8
A_ATIVO = 9
A_COLUNAS = 10

# horarios.txt  ->  professor_email;turma;disciplina;dia;inicio;fim
H_PROFESSOR = 0
H_TURMA = 1
H_DISCIPLINA = 2
H_DIA = 3
H_INICIO = 4
H_FIM = 5
H_COLUNAS = 6

# adaptacoes.txt  ->  aluno;professor_email;formato;versao;texto
D_ALUNO = 0
D_PROFESSOR = 1
D_FORMATO = 2
D_VERSAO = 3
D_TEXTO = 4
D_COLUNAS = 5

# ---------------------------------------------------------------------------
# Listas fixas (catálogos)
# ---------------------------------------------------------------------------
PAPEIS = ["coordenador", "professor", "nucleo"]
NECESSIDADES = ["TEA", "TDAH", "Dislexia", "Deficiência visual"]
FORMATOS = ["Simples", "Resumo", "Visual", "Áudio"]
DIAS = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]
DICAS = [
    "faça pausas curtas entre as etapas.",
    "leia em voz alta, devagar.",
    "use um marcador de texto nas palavras importantes.",
    "peça ajuda quando travar, isso faz parte.",
]

LIMITE_ENTRADA = 12000  # caracteres do material que a "IA" lê
LIMITE_FRASES = 15  # frases que a "IA" usa

COM_ACENTO = "áàâãäéèêëíìîïóòôõöúùûüç"
SEM_ACENTO = "aaaaaeeeeiiiiooooouuuuc"


# ===========================================================================
# 1. FUNÇÕES AUXILIARES (strings e entrada de dados)
# ===========================================================================
def limpar(texto):
    """Tira espaços das pontas e remove ';' e quebras de linha, que quebrariam o arquivo."""
    texto = texto.strip()
    texto = texto.replace(";", " ")
    texto = texto.replace("\n", " ")
    return texto


def normalizar(texto):
    """Deixa minúsculo e sem acento, para a busca não diferenciar 'Ana' de 'ANA' nem 'é' de 'e'."""
    texto = texto.lower().strip()
    resultado = ""
    for letra in texto:
        posicao = COM_ACENTO.find(letra)
        if posicao >= 0:
            resultado = resultado + SEM_ACENTO[posicao]
        else:
            resultado = resultado + letra
    return resultado


def ler_numero(mensagem, minimo, maximo):
    """Pede um número inteiro e só devolve quando estiver entre minimo e maximo."""
    while True:
        try:
            numero = int(input(mensagem))
        except ValueError:
            # int("abc") dá ValueError: o programa avisa e pergunta de novo.
            print("Digite apenas números.")
        else:
            # O else só roda quando NÃO houve erro.
            if minimo <= numero <= maximo:
                return numero
            print(f"Escolha um número entre {minimo} e {maximo}.")


def ler_texto_obrigatorio(mensagem):
    """Repete a pergunta até a pessoa digitar alguma coisa."""
    while True:
        texto = limpar(input(mensagem))
        if texto != "":
            return texto
        print("Este campo não pode ficar vazio.")


def hora_valida(texto):
    """Confere se o texto é uma hora no formato HH:MM (ex.: 08:30)."""
    if len(texto) != 5 or texto[2] != ":":
        return False
    hora = texto[0:2]
    minuto = texto[3:5]
    if not hora.isdigit() or not minuto.isdigit():
        return False
    return int(hora) < 24 and int(minuto) < 60


def escolher_da_lista(titulo, opcoes):
    """Mostra uma lista numerada e devolve a posição (0, 1, 2...) da opção escolhida."""
    print(titulo)
    for i in range(len(opcoes)):
        print(f"  {i + 1} - {opcoes[i]}")
    escolha = ler_numero("Escolha: ", 1, len(opcoes))
    return escolha - 1


def dia_de_hoje():
    """0 = segunda ... 6 = domingo."""
    return time.localtime().tm_wday


# ===========================================================================
# 2. ARQUIVOS (ler e salvar as matrizes)
# ===========================================================================
def ler_matriz(nome_arquivo, colunas):
    """Lê um .txt e devolve uma matriz. Devolve None se o arquivo ainda não existe."""
    matriz = []
    try:
        with open(nome_arquivo, "r", encoding="utf-8") as arquivo:
            linhas = arquivo.readlines()
    except FileNotFoundError:
        return None
    for linha in linhas:
        linha = linha.strip()
        if linha != "":
            campos = linha.split(";")
            # Ignora linhas estragadas (com número de campos diferente do esperado).
            if len(campos) == colunas:
                matriz.append(campos)
    return matriz


def salvar_matriz(nome_arquivo, matriz):
    """Grava a matriz inteira no .txt (uma linha por registro)."""
    try:
        with open(nome_arquivo, "w", encoding="utf-8") as arquivo:
            for linha in matriz:
                arquivo.write(";".join(linha) + "\n")
    except OSError:
        print(f"Atenção: não consegui salvar o arquivo {nome_arquivo}.")


def carregar_usuarios():
    matriz = ler_matriz(ARQ_USUARIOS, U_COLUNAS)
    if matriz is None:
        # Primeira execução: cria usuários de teste (um de cada papel).
        matriz = [
            ["Coordenação Escola", "coordenacao@escola.com", "solution123", "coordenador", "0"],
            ["Francisco Souza", "francisco@escola.com", "solution123", "professor", "0"],
            ["Joana Lima", "joana@escola.com", "solution123", "professor", "0"],
            ["Núcleo Psicopedagógico", "nucleo@escola.com", "solution123", "nucleo", "0"],
        ]
        salvar_matriz(ARQ_USUARIOS, matriz)
    return matriz


def carregar_alunos():
    matriz = ler_matriz(ARQ_ALUNOS, A_COLUNAS)
    if matriz is None:
        # Alunos FICTÍCIOS para ter o que mostrar.
        matriz = [
            ["Ana Beatriz", "7º B", "TEA", "Visual,Simples", "Aprende com exemplos visuais.",
             "Muda de atividade com dificuldade.", "francisco@escola.com", "0", "", "1"],
            ["Lucas Martins", "7º B", "TDAH", "Resumo", "Entende melhor com instruções curtas.",
             "Perde o foco em textos longos.", "francisco@escola.com", "1", "Faltou três aulas seguidas", "1"],
            ["Sofia Costa", "8º A", "Dislexia", "Áudio,Simples", "Gosta de ouvir a leitura.",
             "Troca letras ao ler.", "joana@escola.com", "0", "", "1"],
            ["Pedro Alves", "8º A", "TDAH,Dislexia", "Resumo,Áudio", "Funciona bem em duplas.",
             "Cansa rápido ao ler.", "joana@escola.com", "0", "", "1"],
        ]
        salvar_matriz(ARQ_ALUNOS, matriz)
    return matriz


def carregar_horarios():
    matriz = ler_matriz(ARQ_HORARIOS, H_COLUNAS)
    if matriz is None:
        # Grade de teste: cada professor tem duas aulas de segunda a sexta.
        matriz = []
        for dia in range(5):
            matriz.append(["francisco@escola.com", "7º B", "Ciências", str(dia), "08:00", "08:50"])
            matriz.append(["francisco@escola.com", "8º A", "Ciências", str(dia), "10:00", "10:50"])
            matriz.append(["joana@escola.com", "8º A", "História", str(dia), "09:00", "09:50"])
        salvar_matriz(ARQ_HORARIOS, matriz)
    return matriz


def carregar_adaptacoes():
    matriz = ler_matriz(ARQ_ADAPTACOES, D_COLUNAS)
    if matriz is None:
        matriz = []
    return matriz


# ===========================================================================
# 3. LOGIN, TERMOS (LGPD) E EQUIPE  (entregas #3, #4 e #11)
# ===========================================================================
def fazer_login(usuarios):
    """Dá 3 tentativas. Devolve a POSIÇÃO do usuário na matriz, ou -1 se errar as 3 vezes."""
    for tentativa in range(3):
        email = input("E-mail: ").strip().lower()
        senha = input("Senha: ")
        for i in range(len(usuarios)):
            if usuarios[i][U_EMAIL] == email and usuarios[i][U_SENHA] == senha:
                return i
        print(f"E-mail ou senha incorretos. Tentativa {tentativa + 1} de 3.")
    return -1


def aceitar_termos(usuarios, posicao):
    """LGPD: no primeiro acesso a pessoa precisa aceitar os termos. Devolve True se aceitou."""
    if usuarios[posicao][U_ACEITOU] == "1":
        return True
    print("\n--- Termos de uso e privacidade (resumo) ---")
    print("Usamos só os dados necessários. Nunca coloque laudo ou diagnóstico.")
    print("Ao adaptar um material, o nome do aluno NÃO é enviado à IA.")
    resposta = input("Você aceita? (s/n): ").strip().lower()
    if resposta != "s":
        return False
    usuarios[posicao][U_ACEITOU] = "1"
    salvar_matriz(ARQ_USUARIOS, usuarios)
    return True


def posicao_do_email(usuarios, email):
    """Devolve a posição do e-mail na matriz de usuários, ou -1 se não existir."""
    for i in range(len(usuarios)):
        if usuarios[i][U_EMAIL] == email:
            return i
    return -1


def nome_do_professor(usuarios, email):
    posicao = posicao_do_email(usuarios, email)
    if posicao == -1:
        return "(sem professor)"
    return usuarios[posicao][U_NOME]


def cadastrar_equipe(usuarios):
    """Coordenação cadastra coordenador, professor ou membro do núcleo (#3 e #4)."""
    papel = PAPEIS[escolher_da_lista("Qual o papel?", ["Coordenador", "Professor", "Núcleo psicopedagógico"])]
    nome = ler_texto_obrigatorio("Nome: ")

    while True:
        email = limpar(input("E-mail: ")).lower()
        if "@" not in email or "." not in email:
            print("E-mail inválido.")
        elif posicao_do_email(usuarios, email) != -1:
            print("Já existe uma pessoa cadastrada com este e-mail.")
        else:
            break

    while True:
        senha = limpar(input("Senha provisória (mínimo 6 caracteres): "))
        if len(senha) >= 6:
            break
        print("Senha curta demais.")

    usuarios.append([nome, email, senha, papel, "0"])
    salvar_matriz(ARQ_USUARIOS, usuarios)
    print(f"{nome} cadastrado como {papel}.")


def listar_equipe(usuarios):
    print("\nEquipe:")
    for i in range(len(usuarios)):
        print(f"  {usuarios[i][U_NOME]} - {usuarios[i][U_EMAIL]} ({usuarios[i][U_PAPEL]})")


def emails_dos_professores(usuarios):
    """Lista só com os e-mails de quem tem papel de professor."""
    emails = []
    for linha in usuarios:
        if linha[U_PAPEL] == "professor":
            emails.append(linha[U_EMAIL])
    return emails


# ===========================================================================
# 4. ALUNOS: cadastro, visibilidade, busca e atenção  (entregas #5, #6 e #10)
# ===========================================================================
def alunos_visiveis(usuario, alunos):
    """Devolve as POSIÇÕES dos alunos ativos que esta pessoa pode ver.
    Coordenação e núcleo veem todos; o professor só vê os dele."""
    posicoes = []
    for i in range(len(alunos)):
        if alunos[i][A_ATIVO] != "1":
            continue
        if usuario[U_PAPEL] == "professor" and alunos[i][A_PROFESSOR] != usuario[U_EMAIL]:
            continue
        posicoes.append(i)
    return posicoes


def mostrar_alunos(posicoes, alunos):
    """Mostra uma lista numerada de alunos (a posição 1, 2, 3 é da LISTA, não da matriz)."""
    if len(posicoes) == 0:
        print("Nenhum aluno encontrado.")
        return
    print("\nAlunos:")
    for n in range(len(posicoes)):
        aluno = alunos[posicoes[n]]
        aviso = ""
        if aluno[A_ATENCAO] == "1":
            aviso = "  [ATENÇÃO: " + aluno[A_MOTIVO] + "]"
        print(f"  {n + 1} - {aluno[A_NOME]} | {aluno[A_TURMA]} | {aluno[A_NECESSIDADES]}{aviso}")


def buscar_alunos(usuario, alunos):
    """Lupa de busca (#10): procura o termo no nome, na turma e nas necessidades.
    Devolve as posições encontradas."""
    termo = normalizar(input("Buscar (Enter mostra todos): "))
    encontrados = []
    for i in alunos_visiveis(usuario, alunos):
        texto = alunos[i][A_NOME] + " " + alunos[i][A_TURMA] + " " + alunos[i][A_NECESSIDADES]
        if termo in normalizar(texto):
            encontrados.append(i)
    return encontrados


def escolher_aluno(usuario, alunos):
    """Deixa a pessoa buscar e escolher um aluno. Devolve a posição na matriz, ou -1 se não houver."""
    encontrados = buscar_alunos(usuario, alunos)
    if len(encontrados) == 0:
        print("Nenhum aluno encontrado.")
        return -1
    mostrar_alunos(encontrados, alunos)
    escolha = ler_numero("Qual aluno? (0 para cancelar): ", 0, len(encontrados))
    if escolha == 0:
        return -1
    return encontrados[escolha - 1]


def escolher_varios(titulo, opcoes):
    """Escolhe várias opções (ex.: necessidades). Devolve um texto como 'TEA,TDAH'."""
    escolhidas = []
    print(titulo)
    while True:
        for i in range(len(opcoes)):
            print(f"  {i + 1} - {opcoes[i]}")
        escolha = ler_numero("Número (0 para terminar): ", 0, len(opcoes))
        if escolha == 0:
            break
        if opcoes[escolha - 1] in escolhidas:
            print("Já escolhido.")
        else:
            escolhidas.append(opcoes[escolha - 1])
    return ",".join(escolhidas)


def cadastrar_aluno(usuarios, alunos):
    """Coordenação cadastra aluno e perfil cognitivo (#5). Só descrições do dia a dia, sem laudo."""
    nome = ler_texto_obrigatorio("Nome do aluno: ")
    turma = ler_texto_obrigatorio("Turma (ex.: 7º B): ")
    necessidades = escolher_varios("Necessidades:", NECESSIDADES)
    formatos = escolher_varios("Formatos recomendados:", FORMATOS)
    aprende = limpar(input("Como aprende melhor (opcional): "))
    dificuldades = limpar(input("Principais dificuldades (opcional): "))

    professores = emails_dos_professores(usuarios)
    professor = ""
    if len(professores) > 0:
        nomes = []
        for email in professores:
            nomes.append(nome_do_professor(usuarios, email))
        escolha = escolher_da_lista("Professor que acompanha:", nomes)
        professor = professores[escolha]

    alunos.append([nome, turma, necessidades, formatos, aprende, dificuldades, professor, "0", "", "1"])
    salvar_matriz(ARQ_ALUNOS, alunos)
    print("Aluno cadastrado!")


def marcar_atencao(usuario, alunos):
    """Marca ou desmarca 'precisa de atenção' (#6)."""
    posicao = escolher_aluno(usuario, alunos)
    if posicao == -1:
        return
    aluno = alunos[posicao]
    if aluno[A_ATENCAO] == "1":
        print(f"{aluno[A_NOME]} já está marcado: {aluno[A_MOTIVO]}")
        resposta = input("Desmarcar? (s/n): ").strip().lower()
        if resposta == "s":
            aluno[A_ATENCAO] = "0"
            aluno[A_MOTIVO] = ""
            print("Atenção removida.")
        else:
            return
    else:
        motivo = ler_texto_obrigatorio("Motivo da atenção: ")
        aluno[A_ATENCAO] = "1"
        aluno[A_MOTIVO] = motivo[0:200]
        print("Aluno marcado como 'precisa de atenção'.")
    salvar_matriz(ARQ_ALUNOS, alunos)


def plano_de_apoio(usuario, alunos):
    """Sugestões de apoio (plano com IA do núcleo). Usa só necessidades e formatos, nunca o nome."""
    posicao = escolher_aluno(usuario, alunos)
    if posicao == -1:
        return
    aluno = alunos[posicao]
    necessidades = aluno[A_NECESSIDADES]
    print(f"\nSugestões de apoio para {aluno[A_NOME]}:")
    if "TEA" in necessidades:
        print("- Avise antes de mudar de atividade e use instruções numeradas.")
    if "TDAH" in necessidades:
        print("- Divida a tarefa em etapas curtas, com pausas entre elas.")
    if "Dislexia" in necessidades:
        print("- Prefira letras maiores, frases curtas e leitura em voz alta.")
    if "Deficiência visual" in necessidades:
        print("- Ofereça o material em áudio e com contraste alto.")
    if necessidades == "":
        print("- Cadastre uma necessidade para receber sugestões.")
    print("Formatos recomendados: " + aluno[A_FORMATOS])


# ===========================================================================
# 5. HORÁRIOS DAS AULAS  (entrega #6)
# ===========================================================================
def cadastrar_horario(usuarios, horarios):
    professores = emails_dos_professores(usuarios)
    if len(professores) == 0:
        print("Cadastre um professor antes.")
        return
    nomes = []
    for email in professores:
        nomes.append(nome_do_professor(usuarios, email))
    professor = professores[escolher_da_lista("Professor:", nomes)]
    turma = ler_texto_obrigatorio("Turma (ex.: 7º B): ")
    disciplina = ler_texto_obrigatorio("Disciplina: ")
    dia = escolher_da_lista("Dia da semana:", DIAS)

    while True:
        inicio = input("Início (HH:MM): ").strip()
        fim = input("Fim (HH:MM): ").strip()
        if not hora_valida(inicio) or not hora_valida(fim):
            print("Use o formato HH:MM, por exemplo 08:30.")
        elif fim <= inicio:
            print("O fim precisa ser depois do início.")
        else:
            break

    horarios.append([professor, turma, disciplina, str(dia), inicio, fim])
    salvar_matriz(ARQ_HORARIOS, horarios)
    print("Horário cadastrado!")


def aulas_de_hoje(horarios, usuarios, email_professor):
    """Devolve linhas de texto das aulas de hoje, em ordem de horário.
    Se email_professor for "", traz as aulas de todos."""
    linhas = []
    for h in horarios:
        if h[H_DIA] != str(dia_de_hoje()):
            continue
        if email_professor != "" and h[H_PROFESSOR] != email_professor:
            continue
        linha = h[H_INICIO] + "-" + h[H_FIM] + "  " + h[H_DISCIPLINA] + " (" + h[H_TURMA] + ")"
        if email_professor == "":
            linha = linha + " - " + nome_do_professor(usuarios, h[H_PROFESSOR])
        linhas.append(linha)
    linhas.sort()  # as horas começam a linha, então ordenar o texto ordena por horário
    return linhas


# ===========================================================================
# 6. PAINÉIS  (entregas #9 e #12)
# ===========================================================================
def mostrar_aulas(linhas):
    print("\nAulas de hoje:")
    if len(linhas) == 0:
        print("  Sem aulas hoje.")
    for linha in linhas:
        print("  " + linha)


def painel_professor(usuario, usuarios, alunos, horarios, adaptacoes):
    meus = alunos_visiveis(usuario, alunos)
    feitas = 0
    for d in adaptacoes:
        if d[D_PROFESSOR] == usuario[U_EMAIL]:
            feitas = feitas + 1

    print(f"\n=== Painel do professor - {usuario[U_NOME]} ===")
    print(f"Meus alunos: {len(meus)} | Adaptações feitas: {feitas}")
    mostrar_aulas(aulas_de_hoje(horarios, usuarios, usuario[U_EMAIL]))

    print("\nAdaptação rápida (primeiros alunos):")
    for n in range(len(meus)):
        if n >= 6:
            print("  ... use 'Adaptar material' para ver todos.")
            break
        print(f"  {alunos[meus[n]][A_NOME]} ({alunos[meus[n]][A_NECESSIDADES]})")

    print("\nPrecisam de atenção:")
    achou = False
    for i in meus:
        if alunos[i][A_ATENCAO] == "1":
            print(f"  {alunos[i][A_NOME]} - {alunos[i][A_MOTIVO]}")
            achou = True
    if not achou:
        print("  Ninguém no momento.")


def painel_coordenacao(usuario, usuarios, alunos, horarios):
    professores = len(emails_dos_professores(usuarios))
    nucleo = 0
    for u in usuarios:
        if u[U_PAPEL] == "nucleo":
            nucleo = nucleo + 1
    ativos = alunos_visiveis(usuario, alunos)
    atencao = 0
    for i in ativos:
        if alunos[i][A_ATENCAO] == "1":
            atencao = atencao + 1

    print(f"\n=== Painel da coordenação - {usuario[U_NOME]} ===")
    print(f"Professores: {professores} | Núcleo: {nucleo} | Alunos ativos: {len(ativos)} | Precisam de atenção: {atencao}")
    mostrar_aulas(aulas_de_hoje(horarios, usuarios, ""))

    print("\nAlunos por necessidade:")
    for necessidade in NECESSIDADES:
        total = 0
        for i in ativos:
            if necessidade in alunos[i][A_NECESSIDADES].split(","):
                total = total + 1
        print(f"  {necessidade}: {total}")


def mostrar_painel(usuario, usuarios, alunos, horarios, adaptacoes):
    if usuario[U_PAPEL] == "professor":
        painel_professor(usuario, usuarios, alunos, horarios, adaptacoes)
    elif usuario[U_PAPEL] == "coordenador":
        painel_coordenacao(usuario, usuarios, alunos, horarios)


# ===========================================================================
# 7. A "IA" SIMULADA E AS ADAPTAÇÕES  (entregas #7 e #8)
# ===========================================================================
def separar_frases(texto):
    """Quebra o texto em frases usando . ! ? como separadores (no máximo LIMITE_FRASES)."""
    texto = texto[0:LIMITE_ENTRADA]
    texto = texto.replace("!", ".").replace("?", ".")
    frases = []
    for pedaco in texto.split("."):
        pedaco = pedaco.strip()
        if pedaco != "" and len(frases) < LIMITE_FRASES:
            frases.append(pedaco)
    return frases


def destacar_longas(frase):
    """Palavras com 8 letras ou mais ficam em MAIÚSCULAS."""
    novas = []
    for palavra in frase.split():
        if len(palavra) >= 8:
            novas.append(palavra.upper())
        else:
            novas.append(palavra)
    return " ".join(novas)


def formato_simples(frases):
    linhas = ["TEXTO EM FRASES CURTAS", ""]
    for frase in frases:
        if len(frase.split()) > 12 and ", " in frase:
            # Frase longa: quebra nas vírgulas.
            for parte in frase.split(", "):
                linhas.append(parte.strip() + ".")
        else:
            linhas.append(frase + ".")
        linhas.append("")
    return linhas


def formato_resumo(frases):
    linhas = ["RESUMO", ""]
    for i in range(len(frases)):
        if i >= 3:
            break
        linhas.append("- " + frases[i])
    palavras_chave = []
    for frase in frases:
        for palavra in frase.split():
            palavra = palavra.strip(",;:").lower()
            if len(palavra) >= 8 and palavra not in palavras_chave and len(palavras_chave) < 5:
                palavras_chave.append(palavra)
    linhas.append("")
    linhas.append("Palavras-chave: " + ", ".join(palavras_chave))
    return linhas


def formato_visual(frases):
    linhas = ["ESQUEMA PARA MARCAR", ""]
    for frase in frases:
        linhas.append("[ ] " + destacar_longas(frase))
    return linhas


def formato_audio(frases):
    linhas = ["ROTEIRO PARA LER EM VOZ ALTA (... = respire)", ""]
    for frase in frases:
        linhas.append(frase + "...")
    return linhas


def gerar_adaptacao(texto, formato, necessidades):
    """A 'IA'. Recebe SÓ o texto, o formato e as necessidades. O nome do aluno nunca chega aqui (LGPD)."""
    frases = separar_frases(texto)
    if len(frases) == 0:
        return ""

    if formato == "Resumo":
        linhas = formato_resumo(frases)
    elif formato == "Visual":
        linhas = formato_visual(frases)
    elif formato == "Áudio":
        linhas = formato_audio(frases)
    else:
        linhas = formato_simples(frases)

    # Um toque extra conforme a necessidade do aluno.
    if "TEA" in necessidades:
        linhas.append("")
        linhas.append(f"Aviso: são {len(frases)} frases. Vá de uma em uma.")
    if "TDAH" in necessidades:
        linhas.append("")
        linhas.append("Foco: leia 3 frases, pause e depois continue.")
    linhas.append("")
    linhas.append("Dica: " + random.choice(DICAS))
    return "\n".join(linhas)


def ler_material():
    """Pega o texto do material: digitado ou lido de um arquivo .txt."""
    escolha = escolher_da_lista("Como enviar o material?", ["Digitar o texto", "Ler de um arquivo .txt"])
    if escolha == 0:
        return input("Cole ou digite o texto: ").strip()

    nome_arquivo = input("Nome do arquivo (ex.: aula.txt): ").strip()
    try:
        with open(nome_arquivo, "r", encoding="utf-8") as arquivo:
            texto = arquivo.read()
    except FileNotFoundError:
        # Erro de ambiente: o arquivo pode não existir.
        print(f"Arquivo não encontrado: {nome_arquivo}")
        return ""
    except UnicodeDecodeError:
        print("Não consegui ler esse arquivo. Salve como UTF-8 e tente de novo.")
        return ""
    return texto.replace("\n", " ").strip()


def exportar(texto, formato):
    """Salva a adaptação em um .txt novo (o nome leva data e hora). Nunca inclui o nome do aluno."""
    nome_arquivo = "adaptacao_" + time.strftime("%Y%m%d_%H%M%S") + ".txt"
    try:
        with open(nome_arquivo, "w", encoding="utf-8") as arquivo:
            arquivo.write("Formato: " + formato + "\n\n" + texto)
    except OSError:
        print("Não foi possível salvar o arquivo.")
        return ""
    print(f"Arquivo salvo: {nome_arquivo}")
    return nome_arquivo


def guardar_historico(adaptacoes, aluno, usuario, formato, versao, resultado):
    """Guarda a adaptação no histórico. As quebras de linha viram '||' para caber em uma linha."""
    texto_guardado = resultado.replace("\n", "||")
    adaptacoes.append([aluno[A_NOME], usuario[U_EMAIL], formato, str(versao), texto_guardado])
    salvar_matriz(ARQ_ADAPTACOES, adaptacoes)


def adaptar_material(usuario, alunos, adaptacoes):
    posicao = escolher_aluno(usuario, alunos)
    if posicao == -1:
        return
    aluno = alunos[posicao]

    print("Formatos recomendados para este aluno: " + aluno[A_FORMATOS])
    formato = FORMATOS[escolher_da_lista("Formato da adaptação:", FORMATOS)]

    texto = ler_material()
    if len(separar_frases(texto)) == 0:
        print("Não encontrei texto para adaptar.")
        return

    versao = 1
    while True:
        resultado = gerar_adaptacao(texto, formato, aluno[A_NECESSIDADES])
        guardar_historico(adaptacoes, aluno, usuario, formato, versao, resultado)
        print(f"\n--- {formato} para {aluno[A_NOME]} (versão {versao}) ---")
        print(resultado)
        print("----------------------------------------")

        resposta = input("[E]xportar, [R]efazer ou [S]air? ").strip().lower()
        if resposta == "e":
            exportar(resultado, formato)
            return
        if resposta == "r":
            versao = versao + 1
        else:
            return


def minhas_adaptacoes(usuario, adaptacoes):
    """Mostra o histórico do professor e deixa abrir/exportar uma adaptação (#8)."""
    minhas = []
    for i in range(len(adaptacoes)):
        if adaptacoes[i][D_PROFESSOR] == usuario[U_EMAIL]:
            minhas.append(i)
    if len(minhas) == 0:
        print("Você ainda não fez nenhuma adaptação.")
        return

    print("\nSuas adaptações:")
    for n in range(len(minhas)):
        d = adaptacoes[minhas[n]]
        print(f"  {n + 1} - {d[D_ALUNO]} | {d[D_FORMATO]} | versão {d[D_VERSAO]}")
    escolha = ler_numero("Abrir qual? (0 para voltar): ", 0, len(minhas))
    if escolha == 0:
        return
    d = adaptacoes[minhas[escolha - 1]]
    texto = d[D_TEXTO].replace("||", "\n")
    print("\n" + texto)
    resposta = input("Exportar para .txt? (s/n): ").strip().lower()
    if resposta == "s":
        exportar(texto, d[D_FORMATO])


# ===========================================================================
# 8. MENUS E PROGRAMA PRINCIPAL
# ===========================================================================
def menu_do_papel(papel):
    """Cada papel vê opções diferentes (mesma ideia do menu do site)."""
    if papel == "coordenador":
        return ["Ver painel", "Cadastrar pessoa da equipe", "Listar equipe", "Cadastrar aluno e perfil",
                "Cadastrar horário de aula", "Buscar alunos", "Marcar atenção em aluno"]
    if papel == "professor":
        return ["Ver painel", "Adaptar material", "Minhas adaptações", "Buscar alunos",
                "Marcar atenção em aluno"]
    return ["Buscar alunos", "Marcar atenção em aluno", "Plano de apoio do aluno"]


def main():
    print("=== Solution for All (backend simples) ===")
    print("Dados fictícios. Usuários de teste (senha solution123):")
    print("  coordenacao@escola.com | francisco@escola.com | joana@escola.com | nucleo@escola.com\n")

    usuarios = carregar_usuarios()
    alunos = carregar_alunos()
    horarios = carregar_horarios()
    adaptacoes = carregar_adaptacoes()

    posicao = fazer_login(usuarios)
    if posicao == -1:
        print("Muitas tentativas erradas. Encerrando.")
        return
    if not aceitar_termos(usuarios, posicao):
        print("Sem aceitar os termos não é possível usar o sistema.")
        return

    usuario = usuarios[posicao]
    mostrar_painel(usuario, usuarios, alunos, horarios, adaptacoes)

    while True:
        opcoes = menu_do_papel(usuario[U_PAPEL])
        print(f"\nMenu ({usuario[U_PAPEL]})")
        for i in range(len(opcoes)):
            print(f"  {i + 1} - {opcoes[i]}")
        print("  0 - Sair")

        escolha = ler_numero("Escolha: ", 0, len(opcoes))
        if escolha == 0:
            print("Até logo!")
            break

        acao = opcoes[escolha - 1]
        if acao == "Ver painel":
            mostrar_painel(usuario, usuarios, alunos, horarios, adaptacoes)
        elif acao == "Cadastrar pessoa da equipe":
            cadastrar_equipe(usuarios)
        elif acao == "Listar equipe":
            listar_equipe(usuarios)
        elif acao == "Cadastrar aluno e perfil":
            cadastrar_aluno(usuarios, alunos)
        elif acao == "Cadastrar horário de aula":
            cadastrar_horario(usuarios, horarios)
        elif acao == "Buscar alunos":
            mostrar_alunos(buscar_alunos(usuario, alunos), alunos)
        elif acao == "Marcar atenção em aluno":
            marcar_atencao(usuario, alunos)
        elif acao == "Adaptar material":
            adaptar_material(usuario, alunos, adaptacoes)
        elif acao == "Minhas adaptações":
            minhas_adaptacoes(usuario, adaptacoes)
        elif acao == "Plano de apoio do aluno":
            plano_de_apoio(usuario, alunos)


main()
