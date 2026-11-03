"""Modelos do controle de estoque.

Regra central: o saldo (`Produto.quantidade`) só muda através de
`MovimentacaoEstoque`, e as movimentações são um log imutável.
"""
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models


class Categoria(models.Model):
    nome = models.CharField("nome", max_length=80, unique=True)
    descricao = models.CharField("descrição", max_length=255, blank=True)

    class Meta:
        ordering = ["nome"]
        verbose_name = "categoria"
        verbose_name_plural = "categorias"

    def __str__(self):
        return self.nome


class Fornecedor(models.Model):
    razao_social = models.CharField("razão social", max_length=150)
    cnpj = models.CharField("CNPJ", max_length=18, unique=True)
    telefone = models.CharField("telefone", max_length=20, blank=True)
    email = models.EmailField("e-mail", blank=True)
    cep = models.CharField("CEP", max_length=9, blank=True)
    logradouro = models.CharField("logradouro", max_length=150, blank=True)
    bairro = models.CharField("bairro", max_length=80, blank=True)
    cidade = models.CharField("cidade", max_length=80, blank=True)
    uf = models.CharField("UF", max_length=2, blank=True)

    class Meta:
        ordering = ["razao_social"]
        verbose_name = "fornecedor"
        verbose_name_plural = "fornecedores"

    def __str__(self):
        return self.razao_social


class Produto(models.Model):
    codigo_barras = models.CharField(
        "código de barras", max_length=32, unique=True, db_index=True
    )
    nome = models.CharField("nome", max_length=150)
    categoria = models.ForeignKey(
        Categoria,
        verbose_name="categoria",
        on_delete=models.PROTECT,
        related_name="produtos",
    )
    preco_custo = models.DecimalField(
        "preço de custo", max_digits=10, decimal_places=2, default=0
    )
    preco_venda = models.DecimalField(
        "preço de venda", max_digits=10, decimal_places=2, default=0
    )
    estoque_minimo = models.PositiveIntegerField("estoque mínimo", default=0)
    # Saldo atual. Não deve ser editado manualmente: é atualizado pelo
    # serviço `registrar_movimentacao`, dentro de uma transação.
    quantidade = models.PositiveIntegerField("quantidade em estoque", default=0)

    class Meta:
        ordering = ["nome"]
        verbose_name = "produto"
        verbose_name_plural = "produtos"

    def __str__(self):
        return self.nome

    @property
    def abaixo_do_minimo(self):
        """True quando o saldo está abaixo do estoque mínimo configurado."""
        return self.quantidade < self.estoque_minimo

    @property
    def valor_imobilizado(self):
        """Capital imobilizado neste produto: saldo x preço de custo."""
        return self.quantidade * self.preco_custo


class MovimentacaoEstoque(models.Model):
    class Tipo(models.TextChoices):
        ENTRADA = "ENTRADA", "Entrada"
        SAIDA = "SAIDA", "Saída"

    class Motivo(models.TextChoices):
        COMPRA = "COMPRA", "Compra"
        VENDA = "VENDA", "Venda"
        AVARIA_VENCIMENTO = "AVARIA/VENCIMENTO", "Avaria / vencimento"
        AJUSTE = "AJUSTE", "Ajuste de inventário"

    # Motivos que só fazem sentido em um tipo específico de movimentação.
    MOTIVOS_POR_TIPO = {
        Tipo.ENTRADA: {Motivo.COMPRA, Motivo.AJUSTE},
        Tipo.SAIDA: {Motivo.VENDA, Motivo.AVARIA_VENCIMENTO, Motivo.AJUSTE},
    }

    produto = models.ForeignKey(
        Produto,
        verbose_name="produto",
        on_delete=models.PROTECT,
        related_name="movimentacoes",
    )
    fornecedor = models.ForeignKey(
        Fornecedor,
        verbose_name="fornecedor",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="movimentacoes",
    )
    tipo = models.CharField("tipo", max_length=8, choices=Tipo.choices)
    motivo = models.CharField("motivo", max_length=20, choices=Motivo.choices)
    quantidade = models.PositiveIntegerField(
        "quantidade", validators=[MinValueValidator(1)]
    )
    criado_em = models.DateTimeField("criado em", auto_now_add=True, db_index=True)
    observacao = models.CharField("observação", max_length=255, blank=True)

    class Meta:
        ordering = ["-criado_em", "-id"]
        verbose_name = "movimentação de estoque"
        verbose_name_plural = "movimentações de estoque"

    def __str__(self):
        return f"{self.get_tipo_display()} de {self.quantidade} x {self.produto}"

    def clean(self):
        super().clean()
        permitidos = self.MOTIVOS_POR_TIPO.get(self.tipo, set())
        if self.motivo and self.tipo and self.motivo not in permitidos:
            raise ValidationError(
                {"motivo": "Este motivo não é válido para o tipo de movimentação escolhido."}
            )

    def save(self, *args, **kwargs):
        # O log de auditoria não pode ser alterado depois de gravado.
        if not self._state.adding:
            raise PermissionError("Movimentações de estoque são imutáveis.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise PermissionError("Movimentações de estoque não podem ser apagadas.")
