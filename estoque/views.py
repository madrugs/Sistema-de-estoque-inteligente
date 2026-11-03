"""Páginas HTML do sistema (Django Templates)."""
from django.contrib.auth.decorators import login_required
from django.db.models import F
from django.shortcuts import render

from .models import Fornecedor, MovimentacaoEstoque, Produto


def _motivos_por_tipo():
    """Mapa {tipo: [[motivo, rótulo], ...]} para o formulário montar as opções."""
    return {
        tipo: [
            [motivo, rotulo]
            for motivo, rotulo in MovimentacaoEstoque.Motivo.choices
            if motivo in permitidos
        ]
        for tipo, permitidos in MovimentacaoEstoque.MOTIVOS_POR_TIPO.items()
    }


@login_required
def estoque_lista(request):
    produtos = Produto.objects.select_related("categoria")
    total_abaixo = produtos.filter(quantidade__lt=F("estoque_minimo")).count()
    return render(
        request,
        "estoque/estoque.html",
        {
            "secao": "estoque",
            "produtos": produtos,
            "total_abaixo": total_abaixo,
        },
    )


@login_required
def movimentar(request):
    return render(
        request,
        "estoque/movimentar.html",
        {
            "secao": "movimentar",
            "produtos": Produto.objects.select_related("categoria"),
            "fornecedores": Fornecedor.objects.all(),
            "tipos": MovimentacaoEstoque.Tipo.choices,
            "motivos_por_tipo": _motivos_por_tipo(),
        },
    )


@login_required
def historico(request):
    movimentacoes = MovimentacaoEstoque.objects.select_related("produto", "fornecedor")[:100]
    return render(
        request,
        "estoque/historico.html",
        {"secao": "historico", "movimentacoes": movimentacoes},
    )
