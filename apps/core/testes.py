"""
Executor dos testes (python manage.py test).

Garante duas coisas, mesmo que a pessoa tenha a chave do Groq no .env:
1. A IA fica no modo simulado e a chave some durante os testes.
2. Nenhum teste acessa a internet: qualquer conexão a um endereço que não seja
   desta máquina (ou do banco configurado) falha na hora.

Os testes da IA de verdade simulam as respostas do Groq (unittest.mock).
"""

import socket

from django.conf import settings
from django.test.runner import DiscoverRunner

LOCAIS = {"localhost", "127.0.0.1", "::1", "", None}


class InternetBloqueada(RuntimeError):
    pass


class TestesSemInternet(DiscoverRunner):
    def setup_test_environment(self, **kwargs):
        super().setup_test_environment(**kwargs)
        self._configuracao = (settings.IA_PROVEDOR, settings.GROQ_API_KEY)
        settings.IA_PROVEDOR = "simulada"
        settings.GROQ_API_KEY = ""

        permitidos = set(LOCAIS)
        for banco in settings.DATABASES.values():
            permitidos.add(banco.get("HOST"))
        self._getaddrinfo = socket.getaddrinfo
        original = self._getaddrinfo

        def getaddrinfo(host, *args, **kw):
            nome = host.decode() if isinstance(host, bytes) else host
            if nome not in permitidos:
                raise InternetBloqueada(f"Teste tentou acessar a internet ({nome}). Use mock.")
            return original(host, *args, **kw)

        socket.getaddrinfo = getaddrinfo

    def teardown_test_environment(self, **kwargs):
        socket.getaddrinfo = self._getaddrinfo
        settings.IA_PROVEDOR, settings.GROQ_API_KEY = self._configuracao
        super().teardown_test_environment(**kwargs)
