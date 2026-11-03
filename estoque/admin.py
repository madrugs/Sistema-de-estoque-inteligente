from django.contrib import admin

from .models import Categoria, Fornecedor, MovimentacaoEstoque, Produto


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ["nome", "descricao"]
    search_fields = ["nome"]


@admin.register(Fornecedor)
class FornecedorAdmin(admin.ModelAdmin):
    list_display = ["razao_social", "cnpj", "telefone", "email", "cidade", "uf"]
    search_fields = ["razao_social", "cnpj"]

    class Media:
        # Ao digitar o CEP, preenche o endereço consultando o ViaCEP.
        js = ["js/utils.js", "js/fornecedor_cep.js"]


@admin.register(Produto)
class ProdutoAdmin(admin.ModelAdmin):
    list_display = [
        "nome",
        "codigo_barras",
        "categoria",
        "quantidade",
        "estoque_minimo",
        "preco_custo",
        "preco_venda",
    ]
    list_filter = ["categoria"]
    search_fields = ["nome", "codigo_barras"]
    # O saldo só muda por movimentação, então não aparece como campo editável.
    readonly_fields = ["quantidade"]


@admin.register(MovimentacaoEstoque)
class MovimentacaoEstoqueAdmin(admin.ModelAdmin):
    """Log de auditoria: somente leitura."""

    list_display = ["criado_em", "produto", "tipo", "motivo", "quantidade", "fornecedor"]
    list_filter = ["tipo", "motivo"]
    search_fields = ["produto__nome", "produto__codigo_barras", "observacao"]
    date_hierarchy = "criado_em"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
