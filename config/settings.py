"""
Configurações do Solution for All.

Os valores que mudam entre máquinas (chave secreta, banco, debug) vêm do
arquivo .env. Copie .env.example para .env antes de rodar o projeto.
"""

import os
from pathlib import Path

import dj_database_url
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def _env_bool(nome, padrao=False):
    valor = os.getenv(nome)
    if valor is None:
        return padrao
    return valor.strip().lower() in {"1", "true", "sim", "yes", "on"}


DEBUG = _env_bool("DEBUG", padrao=True)

SECRET_KEY = os.getenv("SECRET_KEY", "")
if not SECRET_KEY:
    if not DEBUG:
        raise RuntimeError("Defina SECRET_KEY no .env quando DEBUG=False.")
    # Só para desenvolvimento local. Em produção a chave vem do .env.
    SECRET_KEY = "dev-inseguro-troque-no-env"

ALLOWED_HOSTS = [h.strip() for h in os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",") if h.strip()]
CSRF_TRUSTED_ORIGINS = [o.strip() for o in os.getenv("CSRF_TRUSTED_ORIGINS", "").split(",") if o.strip()]


# Apps --------------------------------------------------------------------

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Apps do Solution for All (ordem = ordem de dependência)
    "apps.core",
    "apps.contas",
    "apps.escola",
    "apps.alunos",
    "apps.materiais",
    "apps.painel",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "apps.core.context_processors.menu",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"


# Banco de dados ------------------------------------------------------------
# SQLite no desenvolvimento; em produção, DATABASE_URL aponta para o PostgreSQL.

DATABASES = {
    "default": dj_database_url.config(
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
        conn_max_age=600,
    )
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# Usuários e login -----------------------------------------------------------

# O usuário customizado precisa existir antes da primeira migration.
AUTH_USER_MODEL = "contas.Usuario"

LOGIN_URL = "contas:entrar"
LOGIN_REDIRECT_URL = "painel:painel"
LOGOUT_REDIRECT_URL = "contas:entrar"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# Idioma e fuso --------------------------------------------------------------

LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Recife"
USE_I18N = True
USE_TZ = True


# Arquivos estáticos e uploads ---------------------------------------------

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"


# E-mail ---------------------------------------------------------------------
# No desenvolvimento, os e-mails (ex.: código de recuperar senha) aparecem no terminal.

EMAIL_BACKEND = os.getenv("EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend")
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "Solution for All <nao-responda@solutionforall.local>")


# Mensagens (avisos de sucesso/erro) ----------------------------------------

from django.contrib.messages import constants as mensagens  # noqa: E402

MESSAGE_TAGS = {
    mensagens.DEBUG: "info",
    mensagens.INFO: "info",
    mensagens.SUCCESS: "sucesso",
    mensagens.WARNING: "aviso",
    mensagens.ERROR: "erro",
}
