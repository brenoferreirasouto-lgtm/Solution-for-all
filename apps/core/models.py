from django.db import models


class ModeloBase(models.Model):
    """Campos de data que toda tabela do Solution for All tem."""

    criado_em = models.DateTimeField("criado em", auto_now_add=True)
    atualizado_em = models.DateTimeField("atualizado em", auto_now=True)

    class Meta:
        abstract = True
