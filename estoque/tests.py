from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase

from .models import Categoria, MovimentacaoEstoque, Produto
from .services import SaldoInsuficienteError, calcular_novo_saldo, registrar_movimentacao

Tipo = MovimentacaoEstoque.Tipo
Motivo = MovimentacaoEstoque.Motivo


def criar_produto(**extra):
    categoria, _ = Categoria.objects.get_or_create(nome="Mercearia")
    dados = {
        "codigo_barras": "7890000000011",
        "nome": "Arroz 5kg",
        "categoria": categoria,
        "preco_custo": Decimal("20.00"),
        "preco_venda": Decimal("28.50"),
        "estoque_minimo": 5,
    }
    dados.update(extra)
    return Produto.objects.create(**dados)


class ProdutoModelTests(TestCase):
    def test_abaixo_do_minimo_quando_saldo_menor_que_minimo(self):
        produto = criar_produto(estoque_minimo=5, quantidade=4)
        self.assertTrue(produto.abaixo_do_minimo)

    def test_nao_abaixo_do_minimo_quando_saldo_igual_ou_maior(self):
        produto = criar_produto(estoque_minimo=5, quantidade=5)
        self.assertFalse(produto.abaixo_do_minimo)

    def test_valor_imobilizado_usa_preco_de_custo(self):
        produto = criar_produto(quantidade=3, preco_custo=Decimal("10.50"))
        self.assertEqual(produto.valor_imobilizado, Decimal("31.50"))


class CalculoDeSaldoTests(TestCase):
    def test_entrada_soma_ao_saldo(self):
        self.assertEqual(calcular_novo_saldo(10, Tipo.ENTRADA, 4), 14)

    def test_saida_subtrai_do_saldo(self):
        self.assertEqual(calcular_novo_saldo(10, Tipo.SAIDA, 4), 6)

    def test_saida_maior_que_saldo_e_bloqueada(self):
        with self.assertRaises(SaldoInsuficienteError):
            calcular_novo_saldo(3, Tipo.SAIDA, 4)

    def test_saida_igual_ao_saldo_zera_estoque(self):
        self.assertEqual(calcular_novo_saldo(4, Tipo.SAIDA, 4), 0)


class RegistrarMovimentacaoTests(TestCase):
    def setUp(self):
        self.produto = criar_produto(quantidade=10)

    def test_entrada_atualiza_saldo_e_grava_log(self):
        registrar_movimentacao(
            produto=self.produto, tipo=Tipo.ENTRADA, motivo=Motivo.COMPRA, quantidade=5
        )
        self.produto.refresh_from_db()
        self.assertEqual(self.produto.quantidade, 15)
        self.assertEqual(MovimentacaoEstoque.objects.count(), 1)

    def test_saida_atualiza_saldo_e_grava_log(self):
        registrar_movimentacao(
            produto=self.produto, tipo=Tipo.SAIDA, motivo=Motivo.VENDA, quantidade=3
        )
        self.produto.refresh_from_db()
        self.assertEqual(self.produto.quantidade, 7)

    def test_saida_sem_saldo_nao_altera_nada(self):
        with self.assertRaises(SaldoInsuficienteError):
            registrar_movimentacao(
                produto=self.produto, tipo=Tipo.SAIDA, motivo=Motivo.VENDA, quantidade=11
            )
        self.produto.refresh_from_db()
        self.assertEqual(self.produto.quantidade, 10)
        self.assertEqual(MovimentacaoEstoque.objects.count(), 0)

    def test_motivo_incompativel_com_tipo_e_recusado(self):
        with self.assertRaises(ValidationError):
            registrar_movimentacao(
                produto=self.produto, tipo=Tipo.ENTRADA, motivo=Motivo.VENDA, quantidade=1
            )
        self.produto.refresh_from_db()
        self.assertEqual(self.produto.quantidade, 10)


class MovimentacaoImutavelTests(TestCase):
    def setUp(self):
        self.produto = criar_produto(quantidade=10)
        self.movimentacao = registrar_movimentacao(
            produto=self.produto, tipo=Tipo.ENTRADA, motivo=Motivo.COMPRA, quantidade=2
        )

    def test_nao_pode_ser_alterada(self):
        self.movimentacao.quantidade = 99
        with self.assertRaises(PermissionError):
            self.movimentacao.save()

    def test_nao_pode_ser_apagada(self):
        with self.assertRaises(PermissionError):
            self.movimentacao.delete()
