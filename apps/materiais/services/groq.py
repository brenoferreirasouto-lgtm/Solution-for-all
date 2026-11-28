"""
Conexão com a API do Groq (entrega #2: IA de verdade).

Usa só a biblioteca padrão do Python (urllib), sem pacote extra. A API do Groq
segue o formato da OpenAI: https://console.groq.com/docs/api-reference

Regras deste módulo:
- A chave (GROQ_API_KEY) nunca vai para logs, mensagens de erro ou telas.
- Toda falha vira IAIndisponivel com uma mensagem em português para a tela.
- Quando o modelo principal bate no limite do plano gratuito (ou fica fora do
  ar), tentamos o modelo reserva, que tem um limite separado.
"""

import json
import logging
import socket
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field

from django.conf import settings

logger = logging.getLogger(__name__)

URL = "https://api.groq.com/openai/v1/chat/completions"
USER_AGENT = "SolutionForAll/1.0 (projeto academico CESAR School)"


class ErroGroq(Exception):
    """Falha numa chamada. `trocar_modelo` diz se vale tentar o modelo reserva."""

    def __init__(self, mensagem, *, trocar_modelo=False, status=None):
        super().__init__(mensagem)
        self.mensagem = mensagem
        self.trocar_modelo = trocar_modelo
        self.status = status


@dataclass(frozen=True)
class Resposta:
    texto: str
    modelo: str
    cortada: bool = False  # a IA parou por limite de tamanho da resposta
    segundos: float = 0.0
    uso: dict = field(default_factory=dict)  # tokens gastos
    limites: dict = field(default_factory=dict)  # quanto ainda resta no plano (cabeçalhos x-ratelimit-*)


def modelos():
    """Modelo principal e, se houver, o reserva (sem repetir)."""
    principal = settings.GROQ_MODELO
    reserva = settings.GROQ_MODELO_RESERVA
    return [principal] + ([reserva] if reserva and reserva != principal else [])


def conversar(sistema, usuario, *, max_tokens, temperatura=0.4):
    """
    Manda o pedido ao modelo principal e, se ele estiver no limite, ao reserva.
    Devolve Resposta ou levanta ErroGroq (com a mensagem da última tentativa).
    """
    erro = None
    for modelo in modelos():
        try:
            return chamar(modelo, sistema, usuario, max_tokens=max_tokens, temperatura=temperatura)
        except ErroGroq as falha:
            erro = falha
            logger.warning("Groq falhou com %s (status %s): %s", modelo, falha.status, falha.mensagem)
            if not falha.trocar_modelo:
                break
    raise erro


def chamar(modelo, sistema, usuario, *, max_tokens, temperatura=0.4):
    """Uma chamada a um modelo. Levanta ErroGroq."""
    chave = settings.GROQ_API_KEY
    if not chave:
        raise ErroGroq("A chave do Groq não está configurada (GROQ_API_KEY no .env).")

    corpo = {
        "model": modelo,
        "messages": [{"role": "system", "content": sistema}, {"role": "user", "content": usuario}],
        "temperature": temperatura,
        "max_completion_tokens": max_tokens,
    }
    if modelo.startswith("openai/gpt-oss"):
        # Modelos que "pensam" antes de responder: pouco raciocínio e só a resposta final no texto.
        corpo["reasoning_effort"] = "low"
        corpo["include_reasoning"] = False

    pedido = urllib.request.Request(
        URL,
        data=json.dumps(corpo).encode("utf-8"),
        method="POST",
        headers={
            "Authorization": f"Bearer {chave}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": USER_AGENT,
        },
    )
    inicio = time.monotonic()
    try:
        with urllib.request.urlopen(pedido, timeout=settings.IA_TIMEOUT) as resposta:
            dados = _ler_json(resposta.read())
            cabecalhos = resposta.headers
    except urllib.error.HTTPError as erro:
        raise _erro_http(erro) from None
    except (TimeoutError, socket.timeout):
        raise ErroGroq("A IA demorou demais para responder. Tente de novo em instantes.") from None
    except urllib.error.URLError as erro:
        if isinstance(erro.reason, (TimeoutError, socket.timeout)):
            raise ErroGroq("A IA demorou demais para responder. Tente de novo em instantes.") from None
        raise ErroGroq("Sem conexão com a IA. Confira a internet e tente de novo.") from None
    except (ConnectionError, OSError):
        raise ErroGroq("Sem conexão com a IA. Confira a internet e tente de novo.") from None
    segundos = time.monotonic() - inicio

    try:
        escolha = dados["choices"][0]
        texto = (escolha.get("message") or {}).get("content") or ""
        motivo_fim = escolha.get("finish_reason")
    except (KeyError, IndexError, TypeError, AttributeError):
        raise ErroGroq("A IA mandou uma resposta em formato inesperado. Tente de novo.", trocar_modelo=True) from None
    if not texto.strip():
        raise ErroGroq("A IA não devolveu texto desta vez. Tente de novo.", trocar_modelo=True)

    return Resposta(
        texto=texto,
        modelo=dados.get("model") or modelo,
        cortada=motivo_fim == "length",
        segundos=segundos,
        uso=dados.get("usage") or {},
        limites={
            nome: cabecalhos.get(f"x-ratelimit-{nome}")
            for nome in ("remaining-requests", "remaining-tokens", "reset-requests", "reset-tokens")
            if cabecalhos.get(f"x-ratelimit-{nome}")
        },
    )


def _ler_json(bruto):
    try:
        return json.loads(bruto.decode("utf-8"))
    except (UnicodeDecodeError, ValueError):
        raise ErroGroq("A IA mandou uma resposta em formato inesperado. Tente de novo.", trocar_modelo=True) from None


def _erro_http(erro):
    """Traduz o erro HTTP do Groq para uma mensagem da tela."""
    status = erro.code
    try:
        detalhe = json.loads(erro.read().decode("utf-8")).get("error") or {}
    except Exception:  # corpo vazio ou que não é JSON
        detalhe = {}
    codigo = str(detalhe.get("code") or "")
    texto = str(detalhe.get("message") or "")

    if status == 401:
        return ErroGroq("A chave do Groq foi recusada. Confira GROQ_API_KEY no .env.", status=status)
    if status == 403:
        return ErroGroq("O Groq bloqueou o acesso. Confira a chave e a conta em console.groq.com.", status=status)
    if status == 404 or codigo == "model_not_found":
        return ErroGroq("O modelo de IA configurado não existe mais no Groq.", trocar_modelo=True, status=status)
    if status == 429 or codigo == "rate_limit_exceeded":
        espera = _segundos_de_espera(erro.headers.get("retry-after"))
        quando = f" Tente de novo em {espera}." if espera else " Tente de novo daqui a pouco."
        if "per day" in texto or "(TPD)" in texto or "(RPD)" in texto:
            mensagem = "O limite diário gratuito da IA acabou." + quando
        elif status == 413:
            mensagem = "O material é grande demais para o limite gratuito da IA. Envie um trecho menor."
        else:
            mensagem = "A IA atingiu o limite de uso gratuito por minuto." + quando
        return ErroGroq(mensagem, trocar_modelo=True, status=status)
    if status in (400, 413) and ("context" in texto or "too large" in texto or status == 413):
        return ErroGroq("O material é grande demais para a IA. Envie um trecho menor.", status=status)
    if status >= 500:
        return ErroGroq("O serviço de IA está fora do ar agora. Tente de novo em instantes.", trocar_modelo=True, status=status)
    return ErroGroq("A IA recusou o pedido. Tente de novo ou avise o grupo.", status=status)


def _segundos_de_espera(valor):
    """'retry-after' vem em segundos. Devolve '40 segundos', '3 minutos' ou ''."""
    try:
        segundos = max(1, round(float(valor)))
    except (TypeError, ValueError):
        return ""
    if segundos < 90:
        return f"{segundos} segundos"
    minutos = round(segundos / 60)
    return f"{minutos} minutos" if minutos < 90 else f"{round(minutos / 60)} horas"
