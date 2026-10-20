"""
Usuário do Solution for All.

Login por e-mail (sem username) e um campo `papel` que define o que a pessoa
vê e pode fazer. Este model precisa existir antes da primeira migration do
projeto: trocar o usuário depois exige corrigir o banco à mão.
"""

from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


class Papel(models.TextChoices):
    COORDENADOR = "COORDENADOR", "Coordenador"
    PROFESSOR = "PROFESSOR", "Professor"
    NUCLEO = "NUCLEO", "Núcleo psicopedagógico"


class UsuarioManager(BaseUserManager):
    use_in_migrations = True

    def _criar(self, email, password, **campos):
        if not email:
            raise ValueError("O e-mail é obrigatório.")
        email = self.normalize_email(email).lower()
        usuario = self.model(email=email, **campos)
        usuario.set_password(password)
        usuario.save(using=self._db)
        return usuario

    def create_user(self, email, password=None, **campos):
        campos.setdefault("is_staff", False)
        campos.setdefault("is_superuser", False)
        return self._criar(email, password, **campos)

    def create_superuser(self, email, password=None, **campos):
        campos.setdefault("is_staff", True)
        campos.setdefault("is_superuser", True)
        campos.setdefault("papel", Papel.COORDENADOR)
        if campos.get("is_staff") is not True or campos.get("is_superuser") is not True:
            raise ValueError("O superusuário precisa de is_staff=True e is_superuser=True.")
        return self._criar(email, password, **campos)


class Usuario(AbstractUser):
    # Remove os campos do usuário padrão que o Solution for All não usa.
    username = None
    first_name = None
    last_name = None

    nome = models.CharField("nome", max_length=150)
    email = models.EmailField("e-mail", unique=True)
    papel = models.CharField("papel", max_length=20, choices=Papel.choices, default=Papel.PROFESSOR)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["nome"]

    objects = UsuarioManager()

    class Meta:
        verbose_name = "usuário"
        verbose_name_plural = "usuários"
        ordering = ["nome"]

    def __str__(self):
        return self.nome or self.email

    def get_full_name(self):
        return self.nome

    def get_short_name(self):
        """'Prof. Francisco Almeida' -> 'Prof. Francisco'; 'Ana Beatriz' -> 'Ana'."""
        palavras = self.nome.split()
        if not palavras:
            return self.email
        titulos = {"prof", "profa", "dr", "dra"}
        if len(palavras) > 1 and palavras[0].lower().rstrip(".") in titulos:
            return " ".join(palavras[:2])
        return palavras[0]

    @property
    def e_coordenador(self):
        return self.papel == Papel.COORDENADOR

    @property
    def e_professor(self):
        return self.papel == Papel.PROFESSOR

    @property
    def e_nucleo(self):
        return self.papel == Papel.NUCLEO
