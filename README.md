# Solution for All

App web para professores adaptarem materiais didáticos com IA para estudantes neurodivergentes e com deficiência, com apoio da coordenação e do núcleo psicopedagógico.

Projeto da cadeira **Projetos 1** (Sistemas de Informação, CESAR School), Grupo 7: Francisco Costa, Matheus Nader, Breno Souto, José Victor e Victor Poggi.

> **Status: entregas 1, 3 e 4.** O projeto roda, o banco e o login funcionam, e a coordenação já cadastra coordenadores, professores e membros do núcleo (tela **Equipe**). As demais telas ainda mostram "Em construção" e dizem qual entrega vai construí-las.

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

Da próxima vez, basta entrar na pasta, ativar o ambiente (passo 2, só a linha `activate`) e rodar o passo 6.

### Usuários de demonstração

Todos com a senha `solution123`. Os dados são fictícios (os nomes de alunos são os do protótipo).

| Papel | E-mail | O que vê |
| --- | --- | --- |
| Coordenador | `coordenacao@escola.com` | Tudo, incluindo Equipe, Horários e Catálogos (`/admin/`) |
| Professor | `francisco@escola.com` | Os próprios alunos e materiais, e a tela Adaptar material |
| Núcleo psicopedagógico | `nucleo@escola.com` | Todos os alunos e materiais, e os Catálogos (cadastra e edita, sem excluir) |

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

Os testes também rodam sozinhos no GitHub (aba **Actions**) a cada push e pull request.

---

## Estrutura

```
Solution-for-all/
├── config/              # settings.py e urls.py do projeto
├── apps/
│   ├── core/            # código comum: permissões, menu, página "em construção", popular_demo
│   ├── contas/          # Usuario (login por e-mail + papel), entrar, sair, recuperar senha
│   ├── escola/          # Turma, Disciplina, Lecionacao, HorarioAula + telas de equipe e horários
│   ├── alunos/          # Aluno, Necessidade, TipoAdaptacao + telas de alunos
│   ├── materiais/       # Material, Adaptacao + services/ia.py (IA simulada)
│   └── painel/          # painel inicial de cada papel
├── templates/
│   ├── base.html
│   ├── layouts/         # auth.html (sem menu) e app.html (topo + menu)
│   ├── partials/        # _topbar, _menu, _marca, _campo, _mensagens
│   └── core/ contas/    # páginas
└── static/              # css/app.css (cores e espaços), js/menu.js, img/
```

Ordem de dependência entre os apps: `contas` → `escola` → `alunos` → `materiais` → `painel`.

### Papéis

| Papel | Pode |
| --- | --- |
| Coordenador | Cadastrar coordenadores, professores, membros do núcleo, alunos e horários; ver tudo; Catálogos completos |
| Professor | Ver os alunos vinculados a ele, adaptar materiais, ver as próprias adaptações |
| Núcleo psicopedagógico | Acompanhar todos os alunos, materiais e adaptações; cadastrar e editar nos Catálogos (alunos, turmas, matérias, necessidades, formatos, horários), sem excluir |

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
| `/alunos/?q=&necessidade=` | Lista de alunos com busca | Todos | #10 |
| `/alunos/novo/` | Novo aluno | Coordenador | #5 |
| `/alunos/<id>/` | Perfil e histórico do aluno | Todos (professor só os seus) | #5 |
| `/alunos/<id>/editar/` | Editar aluno | Coordenador | #5 |
| `/alunos/<id>/arquivar/` (POST) | Arquivar aluno | Coordenador | #5 |
| `/equipe/` | Coordenadores, professores e membros do núcleo | Coordenador | #3/#4 (pronta) |
| `/equipe/coordenadores/novo/` | Novo coordenador | Coordenador | #3 (pronta) |
| `/equipe/professores/novo/` | Novo professor | Coordenador | #4 (pronta) |
| `/equipe/nucleo/novo/` | Novo membro do núcleo | Coordenador | #4 (pronta) |
| `/equipe/<id>/editar/` | Editar membro | Coordenador | #4 (pronta) |
| `/equipe/<id>/desativar/` (POST) | Desativar ou reativar acesso | Coordenador | #4 (pronta) |
| `/horarios/` | Grade de horários | Coordenador | #6 |
| `/horarios/novo/`, `/horarios/<id>/editar/` | Cadastrar e editar horário | Coordenador | #6 |
| `/horarios/<id>/excluir/` (POST) | Excluir horário | Coordenador | #6 |
| `/materiais/adaptar/?aluno=&material=` | Adaptar material com IA | Professor | #7 |
| `/materiais/` | Lista de materiais | Todos | #8 |
| `/materiais/<id>/` | Material e suas adaptações | Todos | #8 |
| `/adaptacoes/<id>/` | Material pronto (Ouvir, Refazer, Exportar) | Todos | #8 |
| `/adaptacoes/<id>/refazer/` (POST) | Gerar nova versão | Professor que criou | #8 |
| `/adaptacoes/<id>/exportar/` | Página para imprimir ou salvar em PDF | Todos | #8 |
| `/privacidade/` | Política de Privacidade (versão 1.0) | Visitante | pronta |
| `/termos/` | Termos de Uso (versão 1.0) | Visitante | pronta |
| `/admin/` | Catálogos: turmas, disciplinas, necessidades, formatos | Coordenador | pronta |

Nos templates, use sempre o nome da rota (`{% url 'alunos:detalhe' aluno.pk %}`), nunca o caminho escrito à mão.

---

## Como pegar uma entrega

1. Atualize o `main` e crie uma branch: `git checkout -b entrega-05-cadastro-alunos`.
2. Ache a view "em construção" da tela no `views.py` do app (ex.: `AlunoNovoView` em `apps/alunos/views.py`).
3. Troque pela view de verdade **mantendo a URL, o nome da rota e os `papeis`**. Os testes em `apps/core/tests.py` checam isso.
4. Crie o template da tela estendendo `layouts/app.html` e usando os partials.
5. Mudou um model? Rode `python manage.py makemigrations` e envie a migration junto.
6. Rode `python manage.py test`, faça commits pequenos e abra um pull request.

## Regras do projeto

- **Não troque o `AUTH_USER_MODEL`.** O usuário customizado (`contas.Usuario`) já está na primeira migration.
- **Só dados fictícios.** Necessidades como TEA e TDAH são dados de saúde de crianças (dado sensível pela LGPD).
- **Termos e Política valem como promessa.** O texto publicado em `/termos/` e `/privacidade/` (em `templates/core/`) descreve o que o app faz hoje. Mudou o comportamento (ex.: passou a guardar logs, ligou uma API de IA, escolheu a hospedagem)? Atualize o texto, a versão e a data em `apps/core/documentos.py`. Os rascunhos originais em PDF estão em `Documents/`.
- **A IA nunca recebe o nome do aluno.** `apps/materiais/services/ia.py` recebe só o texto do material e o formato. Hoje a IA é simulada; a API gratuita é testada à parte (entrega #2).
- **Ações que mudam dados usam POST** com `{% csrf_token %}`, nunca um link.
- **Cores só pelas variáveis** do topo de `static/css/app.css`. O verde `#17705F` passa no contraste com texto branco; o `#1C8874` do protótipo não.
