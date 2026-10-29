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


# Catálogos (o /admin/): quais modelos cada papel gerencia e com quais ações.
# Coordenador faz tudo; o núcleo cadastra e edita, mas não exclui.
CATALOGOS = (
    "escola.turma",
    "escola.disciplina",
    "escola.lecionacao",
    "escola.horarioaula",
    "alunos.necessidade",
    "alunos.tipoadaptacao",
    "alunos.aluno",
)
ACOES_CATALOGO = {
    Papel.COORDENADOR: ("view", "add", "change", "delete"),
    Papel.NUCLEO: ("view", "add", "change"),
}


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

    def save(self, *args, **kwargs):
        # Quem gerencia catálogos entra no /admin/, então precisa de is_staff.
        # O papel manda: o coordenador e o núcleo sempre têm; o professor, nunca
        # (a não ser que seja superusuário).
        self.is_staff = self.is_superuser or self.papel in ACOES_CATALOGO
        update_fields = kwargs.get("update_fields")
        if update_fields is not None and "papel" in update_fields:
            kwargs["update_fields"] = {*update_fields, "is_staff"}
        super().save(*args, **kwargs)

    # Permissões dos catálogos vêm direto do papel (sem precisar de grupos no
    # banco), então vale para qualquer usuário criado, em qualquer tela.
    def _acoes_no_catalogo(self):
        if not self.is_active:
            return ()
        return ACOES_CATALOGO.get(self.papel, ())

    def has_perm(self, perm, obj=None):
        if self.is_active and "." in perm:
            app_label, codename = perm.split(".", 1)
            acao, _, modelo = codename.partition("_")
            if f"{app_label}.{modelo}" in CATALOGOS and acao in self._acoes_no_catalogo():
                return True
        return super().has_perm(perm, obj)

    def has_module_perms(self, app_label):
        if any(c.startswith(f"{app_label}.") for c in CATALOGOS) and self._acoes_no_catalogo():
            return True
        return super().has_module_perms(app_label)

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
