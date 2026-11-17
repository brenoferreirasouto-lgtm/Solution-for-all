"""
Cria dados FICTÍCIOS para testar o app: um usuário de cada papel, turmas,
disciplinas, a grade de horários, os alunos do protótipo e alguns materiais
já adaptados.

    python manage.py popular_demo

Pode rodar mais de uma vez: o que já existe é mantido, e só o que estiver
vazio é preenchido (perfil, plano com IA, data da atenção).
Nunca use dados de alunos reais aqui (LGPD).
"""

from datetime import time

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from apps.alunos.models import Aluno, Necessidade, TipoAdaptacao
from apps.contas.models import Papel, Usuario
from apps.escola.models import DiaSemana, Disciplina, HorarioAula, Lecionacao, Turma
from apps.materiais.models import Adaptacao, Material
from apps.materiais.services.adaptacoes import adaptar, disciplina_do_professor

SENHA_PADRAO = "solution123"

USUARIOS = [
    # e-mail, nome, papel, is_staff/superuser
    ("coordenacao@escola.com", "Coordenação Pedagógica", Papel.COORDENADOR, True),
    ("francisco@escola.com", "Prof. Francisco Almeida", Papel.PROFESSOR, False),
    ("helena@escola.com", "Prof. Helena Rocha", Papel.PROFESSOR, False),
    ("nucleo@escola.com", "Núcleo Psicopedagógico", Papel.NUCLEO, False),
]

# Grade semanal: professor (e-mail), matéria, turma, dia, início, fim.
HORARIOS = [
    ("francisco@escola.com", "Ciências", "7º A", DiaSemana.SEGUNDA, time(8, 0), time(8, 50)),
    ("francisco@escola.com", "Ciências", "7º A", DiaSemana.QUARTA, time(10, 0), time(10, 50)),
    ("francisco@escola.com", "Ciências", "7º B", DiaSemana.TERCA, time(8, 0), time(8, 50)),
    ("francisco@escola.com", "Ciências", "7º B", DiaSemana.QUINTA, time(9, 0), time(9, 50)),
    # Helena só dá aula no 7º A: entrando com ela, aparecem só os alunos dessa turma.
    ("helena@escola.com", "Matemática", "7º A", DiaSemana.TERCA, time(8, 0), time(8, 50)),
    ("helena@escola.com", "Matemática", "7º A", DiaSemana.QUINTA, time(10, 0), time(10, 50)),
    ("helena@escola.com", "Matemática", "7º A", DiaSemana.SEXTA, time(10, 0), time(10, 50)),
]

ALUNOS = [
    # nome, turma, necessidade (slug), formato (slug), motivo da atenção ("" = não precisa)
    ("Ana Beatriz", "7º B", "tea", "simples", "Faltou duas semanas e precisa retomar frações."),
    ("Lucas Martins", "7º B", "tdah", "resumo", "As notas de Ciências caíram no último bimestre."),
    ("Sofia Costa", "7º A", "dislexia", "audio", ""),
    ("Marina Oliveira", "7º A", "tea", "visual", ""),
    ("Maria Júlia", "7º B", "tea", "simples", ""),
    ("Henrique Lima", "7º A", "tdah", "resumo", ""),
    ("Gabriel Souza", "7º B", "dislexia", "audio", ""),
]

# Perfil cognitivo fictício: só o que a escola observa em sala, nada de diagnóstico.
# Henrique e Gabriel ficam sem perfil para mostrar a tela vazia.
PERFIS = {
    "Ana Beatriz": {
        "como_aprende": "Entende melhor com imagens e instruções curtas, uma de cada vez.",
        "dificuldades": "Textos longos e mudanças de atividade sem aviso.",
        "estrategias": "Avisar antes de trocar de atividade e dividir a tarefa em etapas numeradas.",
        "plano_ia": True,
    },
    "Lucas Martins": {
        "como_aprende": "Aprende fazendo: experimentos, jogos e tarefas curtas.",
        "dificuldades": "Manter o foco em explicações longas e organizar o caderno.",
        "estrategias": "Pausas curtas entre as etapas e a lista de passos colada no caderno.",
        "plano_ia": True,
    },
    "Sofia Costa": {
        "como_aprende": "Ouvindo a explicação e conversando sobre o conteúdo.",
        "dificuldades": "Ler textos longos com letra pequena.",
        "estrategias": "Material em áudio, fonte maior e mais tempo para a leitura.",
        "plano_ia": True,
    },
    "Marina Oliveira": {
        "como_aprende": "Com esquemas, mapas mentais e uma rotina previsível.",
        "dificuldades": "Perguntas abertas sem exemplo.",
        "estrategias": "Mostrar um exemplo resolvido antes da atividade.",
    },
    "Maria Júlia": {
        "como_aprende": "Com instruções diretas e exemplos do dia a dia.",
        "dificuldades": "Trabalhos em grupos grandes.",
        "estrategias": "Duplas fixas e um papel definido em cada atividade.",
    },
}

# Materiais de exemplo (texto colado, sem arquivo) e para quem foram adaptados.
MATERIAIS = [
    {
        "professor": "francisco@escola.com",
        "titulo": "Fotossíntese",
        "turma": "7º B",
        "texto": (
            "Fotossíntese\n\n"
            "A fotossíntese é o processo pelo qual as plantas produzem o próprio alimento. Ela acontece "
            "principalmente nas folhas, dentro de estruturas chamadas cloroplastos, que contêm um pigmento "
            "verde chamado clorofila, responsável por captar a energia da luz do sol.\n\n"
            "Para fazer a fotossíntese, a planta precisa de três ingredientes: água, gás carbônico e luz. "
            "A água é absorvida pelas raízes; o gás carbônico entra pelas folhas.\n\n"
            "No final do processo, a planta produz glicose, que serve de alimento, e libera oxigênio no ar. "
            "Por isso as plantas são tão importantes para a vida na Terra!"
        ),
        # aluno, formato, quantas versões, revisada?
        "adaptacoes": [
            ("Ana Beatriz", "simples", 1, True),
            ("Lucas Martins", "resumo", 2, False),
            ("Gabriel Souza", "audio", 1, False),
        ],
    },
    {
        "professor": "francisco@escola.com",
        "titulo": "O ciclo da água",
        "turma": "7º A",
        "texto": (
            "O ciclo da água\n\n"
            "A água do planeta está sempre mudando de lugar e de estado. O calor do sol aquece rios, lagos e "
            "mares, e parte dessa água evapora e sobe como vapor.\n\n"
            "Lá em cima, o vapor esfria e forma pequenas gotas, que se juntam nas nuvens. Esse passo se chama "
            "condensação.\n\n"
            "Quando as gotas ficam pesadas, caem como chuva, neve ou granizo. É a precipitação.\n\n"
            "A água da chuva escorre para os rios ou entra no solo, e o ciclo recomeça."
        ),
        "adaptacoes": [("Marina Oliveira", "visual", 1, True)],
    },
    {
        "professor": "helena@escola.com",
        "titulo": "Frações no dia a dia",
        "turma": "7º A",
        "texto": (
            "Frações no dia a dia\n\n"
            "Uma fração mostra uma parte de um todo. Se uma pizza é cortada em 8 pedaços iguais e você come 3, "
            "você comeu 3/8 da pizza.\n\n"
            "O número de baixo, o denominador, diz em quantas partes iguais o todo foi dividido. O número de "
            "cima, o numerador, diz quantas dessas partes foram usadas.\n\n"
            "Frações aparecem em receitas, no relógio e no dinheiro. Meia hora é 1/2 de uma hora, e 25 centavos "
            "são 1/4 de um real."
        ),
        "adaptacoes": [("Sofia Costa", "audio", 1, False), ("Henrique Lima", "resumo", 1, False)],
    },
]


class Command(BaseCommand):
    help = "Cria dados fictícios de demonstração (só com DEBUG=True)."

    def add_arguments(self, parser):
        parser.add_argument("--senha", default=SENHA_PADRAO, help="Senha dos usuários de demonstração.")
        parser.add_argument("--forcar", action="store_true", help="Roda mesmo com DEBUG=False.")

    @transaction.atomic
    def handle(self, *args, senha, forcar, **options):
        if not settings.DEBUG and not forcar:
            raise CommandError("DEBUG=False. Use --forcar se tiver certeza (nunca em produção).")

        usuarios = {}
        for email, nome, papel, admin in USUARIOS:
            usuario, criado = Usuario.objects.get_or_create(
                email=email,
                defaults={"nome": nome, "papel": papel, "is_staff": admin, "is_superuser": admin},
            )
            if criado:
                usuario.set_password(senha)
                usuario.save()
            usuarios[email] = usuario
        coordenacao = usuarios["coordenacao@escola.com"]

        turmas = {}
        for nome in ("7º A", "7º B"):
            turmas[nome], _ = Turma.objects.get_or_create(nome=nome, ano_letivo=2026)

        professores_da_turma = {nome: set() for nome in turmas}
        for email, materia, turma, dia, inicio, fim in HORARIOS:
            disciplina, _ = Disciplina.objects.get_or_create(nome=materia)
            lecionacao, _ = Lecionacao.objects.get_or_create(
                professor=usuarios[email], turma=turmas[turma], disciplina=disciplina
            )
            HorarioAula.objects.get_or_create(
                lecionacao=lecionacao, dia_semana=dia, hora_inicio=inicio, defaults={"hora_fim": fim}
            )
            professores_da_turma[turma].add(usuarios[email])

        for nome, turma, necessidade, formato, motivo in ALUNOS:
            aluno, criado = Aluno.objects.get_or_create(
                nome=nome, defaults={"turma": turmas[turma], "criado_por": coordenacao}
            )
            if criado:
                aluno.necessidades.add(Necessidade.objects.get(slug=necessidade))
                aluno.formatos.add(TipoAdaptacao.objects.get(slug=formato))
            # Cada aluno é acompanhado pelos professores que dão aula na turma dele.
            aluno.professores.add(*professores_da_turma[aluno.turma.nome])

            # Daqui para baixo só preenche o que estiver vazio.
            perfil = dict(PERFIS.get(nome, {}))
            plano = perfil.pop("plano_ia", False)
            if perfil and not aluno.tem_perfil:
                for campo, valor in perfil.items():
                    setattr(aluno, campo, valor)
            if plano and not aluno.plano_ia_texto:
                aluno.plano_ia = True
                aluno.gerar_plano()
            if criado and motivo:
                aluno.marcar_atencao(motivo, coordenacao)
            elif aluno.precisa_atencao and not aluno.atencao_marcada_em:
                # Marcado antes da entrega #6, quando ainda não se guardava quem e quando.
                aluno.atencao_marcada_em = timezone.now()
                aluno.atencao_marcada_por = coordenacao
            aluno.save()

        self.criar_materiais(usuarios, turmas)

        self.stdout.write(self.style.SUCCESS("Dados de demonstração prontos."))
        self.stdout.write(f"Senha de todos os usuários novos: {senha}")
        for email, _, papel, _ in USUARIOS:
            self.stdout.write(f"  {Papel(papel).label:<24} {email}")

    def criar_materiais(self, usuarios, turmas):
        """Materiais já adaptados (entregas #7 e #8). Só cria as adaptações que faltam."""
        for dados in MATERIAIS:
            professor = usuarios[dados["professor"]]
            material, _ = Material.objects.get_or_create(
                titulo=dados["titulo"],
                professor=professor,
                defaults={
                    "texto_extraido": dados["texto"],
                    "disciplina_id": disciplina_do_professor(professor, turmas[dados["turma"]]),
                },
            )
            for nome, formato, versoes, revisada in dados["adaptacoes"]:
                aluno = Aluno.objects.filter(nome=nome).first()
                tipo = TipoAdaptacao.objects.get(slug=formato)
                if not aluno or Adaptacao.objects.filter(material=material, aluno=aluno, tipo=tipo).exists():
                    continue
                for _ in range(versoes):
                    adaptacao = adaptar(material, aluno, tipo, professor)
                if revisada:
                    adaptacao.revisado_em = timezone.now()
                    adaptacao.save(update_fields=["revisado_em"])
