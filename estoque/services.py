"""Regras de negócio para movimentar o estoque.

Todo ajuste de saldo passa por `registrar_movimentacao`, que grava a
movimentação e atualiza o saldo na mesma transação.
"""
from django.core.exceptions import ValidationError
from django.db import transaction

from .models import MovimentacaoEstoque, Produto


class SaldoInsuficienteError(ValidationError):
    """Lançada quando uma saída pediria mais do que o saldo disponível."""


def calcular_novo_saldo(saldo_atual, tipo, quantidade):
    """Retorna o saldo resultante de uma movimentação, sem tocar no banco.

    Levanta `SaldoInsuficienteError` se a saída for maior que o saldo.
    """
    if tipo == MovimentacaoEstoque.Tipo.ENTRADA:
        return saldo_atual + quantidade
    if quantidade > saldo_atual:
        raise SaldoInsuficienteError(
            {
                "quantidade": (
                    f"Quantidade solicitada ({quantidade}) maior que o saldo "
                    f"em estoque ({saldo_atual})."
                )
            }
        )
    return saldo_atual - quantidade


@transaction.atomic
def registrar_movimentacao(
    *, produto, tipo, motivo, quantidade, fornecedor=None, observacao=""
):
    """Grava uma movimentação e atualiza o saldo do produto.

    O produto é bloqueado com `select_for_update` para que duas saídas
    simultâneas não consigam vender o mesmo saldo duas vezes.
    """
    produto = Produto.objects.select_for_update().get(pk=produto.pk)

    movimentacao = MovimentacaoEstoque(
        produto=produto,
        fornecedor=fornecedor,
        tipo=tipo,
        motivo=motivo,
        quantidade=quantidade,
        observacao=observacao,
    )
    movimentacao.full_clean()

    produto.quantidade = calcular_novo_saldo(produto.quantidade, tipo, quantidade)
    produto.save(update_fields=["quantidade"])
    movimentacao.save()
    return movimentacao
