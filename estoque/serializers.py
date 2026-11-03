from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from .models import Fornecedor, MovimentacaoEstoque, Produto
from .services import registrar_movimentacao


class FornecedorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Fornecedor
        fields = [
            "id",
            "razao_social",
            "cnpj",
            "telefone",
            "email",
            "cep",
            "logradouro",
            "bairro",
            "cidade",
            "uf",
        ]


class ProdutoSerializer(serializers.ModelSerializer):
    categoria_nome = serializers.CharField(source="categoria.nome", read_only=True)
    abaixo_do_minimo = serializers.BooleanField(read_only=True)

    class Meta:
        model = Produto
        fields = [
            "id",
            "codigo_barras",
            "nome",
            "categoria",
            "categoria_nome",
            "preco_custo",
            "preco_venda",
            "estoque_minimo",
            "quantidade",
            "abaixo_do_minimo",
        ]
        read_only_fields = ["quantidade"]


class MovimentacaoSerializer(serializers.ModelSerializer):
    """Registra entradas e saídas. O saldo nunca é enviado pelo cliente."""

    produto = serializers.PrimaryKeyRelatedField(queryset=Produto.objects.all())
    fornecedor = serializers.PrimaryKeyRelatedField(
        queryset=Fornecedor.objects.all(), required=False, allow_null=True
    )
    produto_nome = serializers.CharField(source="produto.nome", read_only=True)
    saldo_apos = serializers.IntegerField(source="produto.quantidade", read_only=True)

    class Meta:
        model = MovimentacaoEstoque
        fields = [
            "id",
            "produto",
            "produto_nome",
            "fornecedor",
            "tipo",
            "motivo",
            "quantidade",
            "observacao",
            "criado_em",
            "saldo_apos",
        ]
        read_only_fields = ["id", "criado_em"]

    def create(self, validated_data):
        try:
            return registrar_movimentacao(
                produto=validated_data["produto"],
                fornecedor=validated_data.get("fornecedor"),
                tipo=validated_data["tipo"],
                motivo=validated_data["motivo"],
                quantidade=validated_data["quantidade"],
                observacao=validated_data.get("observacao", ""),
            )
        except DjangoValidationError as exc:
            if hasattr(exc, "error_dict"):
                raise serializers.ValidationError(exc.message_dict)
            raise serializers.ValidationError({"non_field_errors": exc.messages})
