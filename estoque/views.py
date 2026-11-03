"""Páginas HTML do sistema (Django Templates)."""
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Count, DecimalField, ExpressionWrapper, F, Q, Sum
from django.shortcuts import render

from .models import Categoria, Fornecedor, MovimentacaoEstoque, Produto


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


def indicadores_do_painel():
    """Agregações do ORM usadas no painel: Sum, Avg e Count."""
    valor_imobilizado = ExpressionWrapper(
        F("quantidade") * F("preco_custo"),
        output_field=DecimalField(max_digits=16, decimal_places=2),
    )
    totais = Produto.objects.aggregate(
        capital_imobilizado=Sum(valor_imobilizado),
        total_produtos=Count("id"),
        total_unidades=Sum("quantidade"),
        preco_medio_venda=Avg("preco_venda"),
        produtos_criticos=Count("id", filter=Q(quantidade__lt=F("estoque_minimo"))),
    )
    return {chave: (valor or 0) for chave, valor in totais.items()}


@login_required
def painel(request):
    categorias = Categoria.objects.annotate(volume=Sum("produtos__quantidade")).order_by("nome")
    movimentos = MovimentacaoEstoque.objects.values("tipo").annotate(total=Count("id"))
    contagem_tipos = {linha["tipo"]: linha["total"] for linha in movimentos}
    rotulos_tipos = dict(MovimentacaoEstoque.Tipo.choices)

    grafico_categorias = {
        "labels": [categoria.nome for categoria in categorias],
        "valores": [categoria.volume or 0 for categoria in categorias],
    }
    grafico_movimentos = {
        "labels": [rotulos_tipos[tipo] for tipo in MovimentacaoEstoque.Tipo.values],
        "valores": [contagem_tipos.get(tipo, 0) for tipo in MovimentacaoEstoque.Tipo.values],
    }

    return render(
        request,
        "estoque/painel.html",
        {
            "secao": "painel",
            "indicadores": indicadores_do_painel(),
            "grafico_categorias": grafico_categorias,
            "grafico_movimentos": grafico_movimentos,
            "ultimas_movimentacoes": MovimentacaoEstoque.objects.select_related("produto")[:5],
        },
    )


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
