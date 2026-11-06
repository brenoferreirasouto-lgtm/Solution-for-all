"""
Cria dados FICTÍCIOS para testar o app: um usuário de cada papel, turmas,
disciplinas, a grade de horários e os alunos que aparecem no protótipo.

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

        self.stdout.write(self.style.SUCCESS("Dados de demonstração prontos."))
        self.stdout.write(f"Senha de todos os usuários novos: {senha}")
        for email, _, papel, _ in USUARIOS:
            self.stdout.write(f"  {Papel(papel).label:<24} {email}")
