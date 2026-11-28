"""
Confere se a IA de verdade (Groq) está funcionando com a chave do .env.

    python manage.py testar_ia

Manda um pedido curto a cada modelo configurado (principal e reserva) e mostra
o tempo de resposta e quanto ainda resta do limite gratuito. Não envia dados
de alunos nem de materiais. A chave nunca é mostrada inteira.
"""

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from apps.materiais.services import groq

PEDIDO = "Responda só com a palavra: funcionando"


def chave_mascarada(chave):
    return f"{chave[:4]}…{chave[-4:]}" if len(chave) > 12 else "(curta demais: confira a chave)"


class Command(BaseCommand):
    help = "Testa a conexão com a IA (Groq) usando a chave do .env."

    def handle(self, *args, **options):
        if settings.IA_PROVEDOR != "groq":
            motivo = "IA_PROVEDOR=simulada no .env" if settings.GROQ_API_KEY else "não há GROQ_API_KEY no .env"
            raise CommandError(
                f"A IA de verdade está desligada ({motivo}). O app usa a IA simulada.\n"
                "Para ligar: crie uma chave em https://console.groq.com/keys e coloque no .env:\n"
                "  GROQ_API_KEY=gsk_..."
            )

        self.stdout.write(f"Chave: {chave_mascarada(settings.GROQ_API_KEY)}")
        falhas = 0
        for papel, modelo in zip(("principal", "reserva"), groq.modelos()):
            try:
                resposta = groq.chamar(modelo, "Você é um teste de conexão.", PEDIDO, max_tokens=200, temperatura=0)
            except groq.ErroGroq as erro:
                falhas += 1
                self.stdout.write(self.style.ERROR(f"✗ {modelo} ({papel}): {erro.mensagem}"))
                continue
            texto = " ".join(resposta.texto.split())[:60]
            self.stdout.write(
                self.style.SUCCESS(f"✓ {resposta.modelo} ({papel}) respondeu em {resposta.segundos:.1f} s: {texto!r}")
            )
            if resposta.limites:
                restam = ", ".join(f"{nome}: {valor}" for nome, valor in resposta.limites.items())
                self.stdout.write(f"  Limite gratuito: {restam}")

        if falhas == len(groq.modelos()):
            raise CommandError("Nenhum modelo respondeu. O app vai mostrar o aviso de erro e o botão Refazer.")
        if falhas:
            self.stdout.write(self.style.WARNING("Um modelo falhou; o app usa o outro automaticamente."))
        else:
            self.stdout.write(self.style.SUCCESS("IA pronta para usar."))
