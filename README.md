# Solution for All

App web para professores adaptarem materiais didáticos com IA para estudantes neurodivergentes e com deficiência, com apoio da coordenação e do núcleo psicopedagógico.

Projeto da cadeira **Projetos 1** (Sistemas de Informação, CESAR School), Grupo 7: Francisco Costa, Matheus Nader, Breno Souto, José Victor e Victor Poggi.

> **Status: entregas 1 a 10 e 12.** O projeto roda, o banco e o login funcionam. A coordenação cadastra a equipe (tela **Equipe**) e a grade de **Horários**; coordenação e núcleo cadastram **Alunos** com perfil cognitivo, sugestões da IA e a lista de quem precisa de atenção. O professor **adapta materiais** (PDF, Word ou texto colado), revisa o texto, ouve, refaz e exporta em PDF ou Word. O menu ☰ (barra lateral no desktop) lista os alunos de quem está logado, com uma lupa que filtra enquanto se digita e uma busca completa em **Alunos** (nome ou turma, e necessidade). A IA é de verdade (Groq) quando há uma chave no `.env`; sem chave, o app usa a IA simulada. As demais telas ainda mostram "Em construção" e dizem qual entrega vai construí-las.

---

## Como rodar pela primeira vez

Você precisa de **Python 3.10 a 3.14** (recomendado 3.12) e **Git**. Não há link público ainda: o app roda no seu computador.

```bash
# 1. Baixar o projeto
git clone https://github.com/brenoferreirasouto-lgtm/Solution-for-all.git
cd Solution-for-all

# 2. Criar e ativar o ambiente virtual
python3 -m venv .venv            # Mac/Linux
source .venv/bin/activate        # Mac/Linux
# python -m venv .venv           # Windows
# .venv\Scripts\activate         # Windows (PowerShell ou CMD)
# Com o ambiente ativado, o comando "python" funciona em todos os sistemas.

# 3. Instalar as dependências
pip install -r requirements.txt

# 4. Criar o arquivo de configuração
cp .env.example .env             # Mac/Linux
# copy .env.example .env         # Windows

# 5. Criar o banco e os dados de demonstração
python manage.py migrate
python manage.py popular_demo

# 6. Rodar
python manage.py runserver
```

Deixe o terminal aberto, abra <http://127.0.0.1:8000> no navegador e entre com um dos usuários abaixo. Para parar o servidor, aperte `Ctrl + C` no terminal.

### Ligar a IA de verdade (Groq, gratuito)

Sem esta etapa o app funciona com a IA simulada. Para usar a IA de verdade:

1. Crie uma conta gratuita em <https://console.groq.com> (não pede cartão).
2. Em **API Keys**, clique em **Create API Key** e copie a chave (começa com `gsk_`). Cada pessoa do grupo cria a sua.
3. No arquivo `.env`, preencha `GROQ_API_KEY=gsk_...`. **Nunca** coloque a chave no código nem no GitHub: o `.env` já fica fora do git.
4. Confira com `python manage.py testar_ia`. Deve aparecer "IA pronta para usar".
5. Recomendado (LGPD): em **Settings > Data Controls** no console do Groq, ligue o **Zero Data Retention**.

O plano gratuito tem limite (perto de 30 pedidos por minuto e algumas dezenas de adaptações por dia em cada modelo). Quando o modelo principal (`openai/gpt-oss-120b`) chega no limite, o app usa sozinho o reserva (`openai/gpt-oss-20b`). Se os dois estiverem no limite, a tela mostra o motivo e o botão Refazer. Numa apresentação sem internet, use `IA_PROVEDOR=simulada` no `.env`.

Da próxima vez, basta entrar na pasta, ativar o ambiente (passo 2, só a linha `activate`) e rodar o passo 6. Depois de um `git pull`, rode também `pip install -r requirements.txt` e `python manage.py migrate`: uma entrega pode trazer dependência ou tabela nova (a #7 trouxe o `python-docx`, para ler e gerar arquivos do Word).

### Usuários de demonstração

Todos com a senha `solution123`. Os dados são fictícios (os nomes de alunos são os do protótipo). Já vêm 3 materiais adaptados: Fotossíntese e O ciclo da água (Francisco) e Frações no dia a dia (Helena).

| Papel | E-mail | O que vê |
| --- | --- | --- |
| Coordenador | `coordenacao@escola.com` | Tudo, incluindo Equipe, Horários e Catálogos (`/admin/`) |
| Professor | `francisco@escola.com` | Os próprios alunos (7º A e 7º B) e materiais, e a tela Adaptar material |
| Professor | `helena@escola.com` | Só os alunos do 7º A, onde ela dá Matemática |
| Núcleo psicopedagógico | `nucleo@escola.com` | Todos os alunos e materiais; cadastra e edita alunos e os Catálogos (sem excluir) |

---

## Comandos do dia a dia

| Para quê | Comando |
| --- | --- |
| Rodar o servidor | `python manage.py runserver` |
| Rodar os testes | `python manage.py test` |
| Criar migration depois de mudar um model | `python manage.py makemigrations` |
| Aplicar migrations | `python manage.py migrate` |
| Criar um coordenador de verdade | `python manage.py createsuperuser` |
| Recriar os dados de demonstração | `python manage.py popular_demo` |
| Testar a chave do Groq | `python manage.py testar_ia` |
| Dados de demonstração gerados pelo Groq | `python manage.py popular_demo --com-ia` |

Os testes também rodam sozinhos no GitHub (aba **Actions**) a cada push e pull request. Os testes nunca acessam a internet nem usam a chave do Groq, mesmo que ela esteja no `.env`: as respostas da IA são simuladas.

---

## Estrutura

```
Solution-for-all/
├── config/              # settings.py e urls.py do projeto
├── apps/
│   ├── core/            # código comum: permissões, menu, página "em construção", popular_demo
│   ├── contas/          # Usuario (login por e-mail + papel), entrar, sair, recuperar senha
│   ├── escola/          # Turma, Disciplina, Lecionacao, HorarioAula + telas de equipe e horários
│   ├── alunos/          # Aluno (perfil cognitivo, plano com IA, atenção), Necessidade, TipoAdaptacao + telas
│   ├── materiais/       # Material, Adaptacao + services/: ia.py (pedidos à IA e IA simulada), groq.py (conexão com o Groq), texto.py (lê PDF/Word/txt), adaptacoes.py
│   └── painel/          # painel inicial de cada papel
├── templates/
│   ├── base.html
│   ├── layouts/         # auth.html (sem menu) e app.html (topo + menu)
│   ├── partials/        # _topbar, _menu, _marca, _campo, _campo_marcar, _mensagens
│   └── core/ contas/ escola/ alunos/   # páginas
└── static/              # css/app.css (cores e espaços), js/ (menu, confirmar, adaptar, ouvir, imprimir), img/
```

Ordem de dependência entre os apps: `contas` → `escola` → `alunos` → `materiais` → `painel`.

### Papéis

| Papel | Pode |
| --- | --- |
| Coordenador | Cadastrar coordenadores, professores, membros do núcleo, alunos e horários; arquivar alunos; ver tudo; Catálogos completos |
| Professor | Ver os alunos vinculados a ele (perfil e sugestões da IA, só leitura); adaptar materiais; revisar, refazer e exportar as adaptações que criou; ler as adaptações feitas por colegas para os seus alunos |
| Núcleo psicopedagógico | Acompanhar todos os alunos, materiais e adaptações; cadastrar e editar alunos e o perfil cognitivo; marcar quem precisa de atenção; cadastrar e editar nos Catálogos (alunos, turmas, matérias, necessidades, formatos, horários), sem excluir |

**Catálogos (`/admin/`):** o acesso vem do papel, não de marcar permissões à mão. Quem é coordenador ou núcleo ganha `is_staff` automaticamente ao ser salvo (e perde se mudar para professor), e as permissões de catálogo ficam em `apps/contas/models.py` (`ACOES_CATALOGO`). Para mudar o que cada papel pode fazer lá, edite esse dicionário.

Cada view declara os papéis aceitos (`papeis = COORDENACAO`, `PROFESSOR`, `TODOS`...). Os dados vêm de consultas como `Aluno.objects.visiveis_para(usuario)`: um professor que abrir o id de um aluno que não é dele recebe 404.

---

## Rotas e entregas

| URL | Tela | Quem acessa | Entrega |
| --- | --- | --- | --- |
| `/entrar/` | Login | Visitante | pronta |
| `/sair/` (POST) | Sair | Logado | pronta |
| `/senha/recuperar/`, `/senha/codigo/`, `/senha/nova/` | Recuperar senha por código no e-mail | Visitante | #13 |
| `/painel/` | Painel do professor / da coordenação / do núcleo | Logado | #9 / #12 |
| `/alunos/` | Lista de alunos, com "Precisam de atenção" no topo | Todos (professor só os seus) | #5/#6 (pronta) |
| `/alunos/?q=&necessidade=` | Busca e filtros na lista (ignora acento e maiúscula; nome ou turma) | Todos (professor só os seus) | #10 (pronta) |
| `/alunos/novo/` | Novo aluno com perfil cognitivo | Coordenador e núcleo | #5 (pronta) |
| `/alunos/<id>/` | Perfil, sugestões da IA e histórico do aluno | Todos (professor só os seus) | #5 (pronta) |
| `/alunos/<id>/editar/` | Editar aluno | Coordenador e núcleo | #5 (pronta) |
| `/alunos/<id>/arquivar/` (POST) | Arquivar ou reativar aluno | Coordenador | #5 (pronta) |
| `/alunos/<id>/plano/` (POST) | Gerar de novo as sugestões da IA | Coordenador e núcleo | #5 (pronta) |
| `/alunos/<id>/atencao/` (POST) | Marcar ou tirar da lista de atenção | Coordenador e núcleo | #6 (pronta) |
| `/equipe/` | Coordenadores, professores e membros do núcleo | Coordenador | #3/#4 (pronta) |
| `/equipe/coordenadores/novo/` | Novo coordenador | Coordenador | #3 (pronta) |
| `/equipe/professores/novo/` | Novo professor | Coordenador | #4 (pronta) |
| `/equipe/nucleo/novo/` | Novo membro do núcleo | Coordenador | #4 (pronta) |
| `/equipe/<id>/editar/` | Editar membro | Coordenador | #4 (pronta) |
| `/equipe/<id>/desativar/` (POST) | Desativar ou reativar acesso | Coordenador | #4 (pronta) |
| `/horarios/?turma=` | Grade semanal, filtrável por turma | Coordenador | #6 (pronta) |
| `/horarios/novo/`, `/horarios/<id>/editar/` | Cadastrar e editar horário (sem choque de turma ou professor) | Coordenador | #6 (pronta) |
| `/horarios/<id>/excluir/` (POST) | Excluir horário | Coordenador | #6 (pronta) |
| `/materiais/adaptar/?aluno=&material=` | Adaptar material com IA: aluno, conteúdo (PDF, Word, .txt ou texto colado) e formato | Professor | #7 (pronta) |
| `/materiais/` | Lista de materiais (professor: os seus) | Todos | #8 (pronta) |
| `/materiais/<id>/` | Material, suas adaptações e o texto original | Todos (professor: os seus) | #8 (pronta) |
| `/adaptacoes/<id>/` | Material pronto: revisar e Salvar, Ouvir, Refazer, Exportar | Todos (professor: as suas e as dos seus alunos) | #8 (pronta) |
| `/adaptacoes/<id>/salvar/` (POST) | Salvar o texto revisado | Professor que criou | #8 (pronta) |
| `/adaptacoes/<id>/refazer/` (POST) | Gerar nova versão (a anterior fica no histórico) | Professor que criou | #8 (pronta) |
| `/adaptacoes/<id>/exportar/` | Página para imprimir ou salvar em PDF (sem o nome do aluno) | Todos | #8 (pronta) |
| `/adaptacoes/<id>/exportar/word/` | Baixar em Word (.docx) | Todos | #8 (pronta) |
| `/privacidade/` | Política de Privacidade (versão 1.1) | Visitante | pronta |
| `/termos/` | Termos de Uso (versão 1.0) | Visitante | pronta |
| `/admin/` | Catálogos: turmas, disciplinas, necessidades, formatos | Coordenador | pronta |

Nos templates, use sempre o nome da rota (`{% url 'alunos:detalhe' aluno.pk %}`), nunca o caminho escrito à mão.

---

## Como pegar uma entrega

1. Atualize o `main` e crie uma branch: `git checkout -b entrega-09-painel-professor`.
2. Ache a view "em construção" da tela no `views.py` do app (ex.: `PainelView` em `apps/painel/views.py`).
3. Troque pela view de verdade **mantendo a URL, o nome da rota e os `papeis`**. Os testes em `apps/core/tests.py` checam isso.
4. Crie o template da tela estendendo `layouts/app.html` e usando os partials.
5. Mudou um model? Rode `python manage.py makemigrations` e envie a migration junto.
6. Rode `python manage.py test`, faça commits pequenos e abra um pull request.

## Regras do projeto

- **Não troque o `AUTH_USER_MODEL`.** O usuário customizado (`contas.Usuario`) já está na primeira migration.
- **Só dados fictícios.** Necessidades como TEA e TDAH são dados de saúde de crianças (dado sensível pela LGPD).
- **Termos e Política valem como promessa.** O texto publicado em `/termos/` e `/privacidade/` (em `templates/core/`) descreve o que o app faz hoje. Mudou o comportamento (ex.: passou a guardar logs, ligou uma API de IA, escolheu a hospedagem)? Atualize o texto, a versão e a data em `apps/core/documentos.py`. Os rascunhos originais em PDF estão em `Documents/`.
- **A IA nunca recebe o nome do aluno.** `apps/materiais/services/ia.py` recebe só o texto do material e o formato (`gerar_adaptacao`) ou só as necessidades e os formatos marcados (Plano com IA, `gerar_plano_apoio`). O perfil escrito pela escola e as observações também não vão para a IA. Com `GROQ_API_KEY` no `.env`, os pedidos vão para o Groq (`groq.py`); sem chave, a IA simulada reorganiza o próprio texto. Se o Groq falhar, `IAIndisponivel` leva a mensagem para a tela: a adaptação fica com status Erro e o botão Refazer, e o cadastro do aluno salva mesmo sem o Plano. Trocou de provedor? Atualize a Política (seções 6 a 8).
- **O professor revisa antes de usar.** Toda adaptação abre com o texto editável e o selo "Ainda não revisado" até ele tocar em Salvar (Termos, seção 6). O botão Ouvir usa a voz do navegador, só com vozes em português instaladas no aparelho, para o texto não sair do computador (sem uma voz dessas, o botão não aparece).
- **Exportar não leva dados do aluno.** A página de impressão e o arquivo Word têm só o título, o texto e uma nota de que houve IA.
- **Perfil cognitivo não é prontuário.** Os campos guardam o que a escola observa em sala (como aprende, dificuldades, estratégias). Nada de diagnóstico, CID ou dado de laudo.
- **Ações que mudam dados usam POST** com `{% csrf_token %}`, nunca um link.
- **Cores só pelas variáveis** do topo de `static/css/app.css`. O verde `#17705F` passa no contraste com texto branco; o `#1C8874` do protótipo não.
