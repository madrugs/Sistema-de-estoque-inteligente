"""Endpoints REST (JSON) do controle de estoque."""
from django.db.models import F, Q
from rest_framework import mixins, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from .cep import (
    CepInvalidoError,
    CepNaoEncontradoError,
    ServicoCepIndisponivelError,
    buscar_cep,
)
from .models import Fornecedor, MovimentacaoEstoque, Produto
from .serializers import FornecedorSerializer, MovimentacaoSerializer, ProdutoSerializer

VERDADEIRO = {"1", "true", "sim", "yes"}


class ProdutoViewSet(viewsets.ReadOnlyModelViewSet):
    """Inventário e consulta rápida de produtos.

    Filtros (querystring):
    - `q`: parte do nome ou código de barras completo.
    - `categoria`: id da categoria.
    - `abaixo_minimo=1`: somente produtos com saldo abaixo do mínimo.
    """

    serializer_class = ProdutoSerializer

    def get_queryset(self):
        params = self.request.query_params
        queryset = Produto.objects.select_related("categoria")

        termo = params.get("q", "").strip()
        if termo:
            queryset = queryset.filter(Q(nome__icontains=termo) | Q(codigo_barras=termo))

        categoria = params.get("categoria")
        if categoria:
            queryset = queryset.filter(categoria_id=categoria)

        if params.get("abaixo_minimo", "").lower() in VERDADEIRO:
            queryset = queryset.filter(quantidade__lt=F("estoque_minimo"))

        return queryset


class MovimentacaoViewSet(
    mixins.ListModelMixin, mixins.CreateModelMixin, viewsets.GenericViewSet
):
    """Histórico (somente leitura) e registro de entradas/saídas.

    Não há PUT, PATCH nem DELETE: o log de auditoria é imutável.
    """

    serializer_class = MovimentacaoSerializer

    def get_queryset(self):
        return MovimentacaoEstoque.objects.select_related("produto", "fornecedor")


class FornecedorViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = FornecedorSerializer
    queryset = Fornecedor.objects.all()


class CepView(APIView):
    """Proxy para o ViaCEP: devolve o endereço para preencher o cadastro."""

    def get(self, request, cep):
        try:
            endereco = buscar_cep(cep)
        except CepInvalidoError as exc:
            return Response({"detail": str(exc)}, status=400)
        except CepNaoEncontradoError as exc:
            return Response({"detail": str(exc)}, status=404)
        except ServicoCepIndisponivelError as exc:
            return Response({"detail": str(exc)}, status=503)
        return Response(endereco)
