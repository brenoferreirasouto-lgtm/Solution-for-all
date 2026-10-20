"""
Cria dados FICTÍCIOS para testar o app: um usuário de cada papel, turmas,
disciplina, horários e os alunos que aparecem no protótipo.

    python manage.py popular_demo

Pode rodar mais de uma vez: o que já existe é mantido.
Nunca use dados de alunos reais aqui (LGPD).
"""

from datetime import time

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.alunos.models import Aluno, Necessidade, TipoAdaptacao
from apps.contas.models import Papel, Usuario
from apps.escola.models import DiaSemana, Disciplina, HorarioAula, Lecionacao, Turma

SENHA_PADRAO = "solution123"

USUARIOS = [
    # e-mail, nome, papel, is_staff/superuser
    ("coordenacao@escola.com", "Coordenação Pedagógica", Papel.COORDENADOR, True),
    ("francisco@escola.com", "Prof. Francisco Almeida", Papel.PROFESSOR, False),
    ("nucleo@escola.com", "Núcleo Psicopedagógico", Papel.NUCLEO, False),
]

ALUNOS = [
    # nome, turma, necessidade (slug), formato (slug), precisa de atenção
    ("Ana Beatriz", "7º B", "tea", "simples", True),
    ("Lucas Martins", "7º B", "tdah", "resumo", True),
    ("Sofia Costa", "7º A", "dislexia", "audio", False),
    ("Marina Oliveira", "7º A", "tea", "visual", False),
    ("Maria Júlia", "7º B", "tea", "simples", False),
    ("Henrique Lima", "7º A", "tdah", "resumo", False),
    ("Gabriel Souza", "7º B", "dislexia", "audio", False),
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
            usuarios[papel] = usuario

        professor = usuarios[Papel.PROFESSOR]
        ciencias, _ = Disciplina.objects.get_or_create(nome="Ciências")
        turmas = {}
        for nome in ("7º A", "7º B"):
            turmas[nome], _ = Turma.objects.get_or_create(nome=nome, ano_letivo=2026)
            lecionacao, _ = Lecionacao.objects.get_or_create(
                professor=professor, turma=turmas[nome], disciplina=ciencias
            )
            HorarioAula.objects.get_or_create(
                lecionacao=lecionacao,
                dia_semana=DiaSemana.SEGUNDA if nome == "7º A" else DiaSemana.TERCA,
                hora_inicio=time(8, 0),
                defaults={"hora_fim": time(8, 50)},
            )

        for nome, turma, necessidade, formato, atencao in ALUNOS:
            aluno, criado = Aluno.objects.get_or_create(
                nome=nome,
                defaults={
                    "turma": turmas[turma],
                    "precisa_atencao": atencao,
                    "motivo_atencao": "Acompanhar aprendizagem" if atencao else "",
                    "criado_por": usuarios[Papel.COORDENADOR],
                },
            )
            if criado:
                aluno.necessidades.add(Necessidade.objects.get(slug=necessidade))
                aluno.formatos.add(TipoAdaptacao.objects.get(slug=formato))
                aluno.professores.add(professor)

        self.stdout.write(self.style.SUCCESS("Dados de demonstração prontos."))
        self.stdout.write(f"Senha de todos os usuários novos: {senha}")
        for email, _, papel, _ in USUARIOS:
            self.stdout.write(f"  {Papel(papel).label:<24} {email}")
