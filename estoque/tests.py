import json
from decimal import Decimal
from unittest import mock

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from .cep import normalizar_cep
from .models import Categoria, Fornecedor, MovimentacaoEstoque, Produto
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


class CepNormalizacaoTests(TestCase):
    def test_remove_pontuacao(self):
        self.assertEqual(normalizar_cep("01001-000"), "01001000")

    def test_rejeita_quantidade_errada_de_digitos(self):
        with self.assertRaises(ValueError):
            normalizar_cep("1234")


class FakeResposta:
    """Imita o retorno de `urlopen` usado como gerenciador de contexto."""

    def __init__(self, corpo):
        self._corpo = corpo

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return self._corpo.encode("utf-8")


class ApiTestCase(TestCase):
    def setUp(self):
        self.usuario = get_user_model().objects.create_user("operador", password="senha-forte-123")
        self.client.force_login(self.usuario)
        self.categoria = Categoria.objects.create(nome="Bebidas")
        self.produto = criar_produto(
            categoria=self.categoria, codigo_barras="7891000000001", nome="Refrigerante 2L",
            quantidade=10, estoque_minimo=4,
        )


class ProdutoApiTests(ApiTestCase):
    def test_lista_retorna_200_e_json_esperado(self):
        resposta = self.client.get(reverse("produto-list"))
        self.assertEqual(resposta.status_code, 200)
        item = resposta.json()[0]
        self.assertEqual(item["nome"], "Refrigerante 2L")
        self.assertEqual(item["categoria_nome"], "Bebidas")
        self.assertFalse(item["abaixo_do_minimo"])

    def test_busca_por_nome_e_codigo_de_barras(self):
        por_nome = self.client.get(reverse("produto-list"), {"q": "refri"}).json()
        por_codigo = self.client.get(reverse("produto-list"), {"q": "7891000000001"}).json()
        self.assertEqual(len(por_nome), 1)
        self.assertEqual(len(por_codigo), 1)

    def test_filtra_produtos_abaixo_do_minimo(self):
        self.produto.quantidade = 2
        self.produto.save()
        resposta = self.client.get(reverse("produto-list"), {"abaixo_minimo": "1"})
        self.assertEqual(len(resposta.json()), 1)
        self.assertTrue(resposta.json()[0]["abaixo_do_minimo"])

    def test_detalhe_retorna_200(self):
        resposta = self.client.get(reverse("produto-detail", args=[self.produto.pk]))
        self.assertEqual(resposta.status_code, 200)

    def test_exige_autenticacao(self):
        self.client.logout()
        resposta = self.client.get(reverse("produto-list"))
        self.assertIn(resposta.status_code, {401, 403})


class MovimentacaoApiTests(ApiTestCase):
    def registrar(self, **dados):
        corpo = {
            "produto": self.produto.pk,
            "tipo": "SAIDA",
            "motivo": "VENDA",
            "quantidade": 3,
        }
        corpo.update(dados)
        return self.client.post(
            reverse("movimentacao-list"),
            data=json.dumps(corpo),
            content_type="application/json",
        )

    def test_saida_valida_retorna_201_com_saldo_atualizado(self):
        resposta = self.registrar()
        self.assertEqual(resposta.status_code, 201)
        self.assertEqual(resposta.json()["saldo_apos"], 7)
        self.produto.refresh_from_db()
        self.assertEqual(self.produto.quantidade, 7)

    def test_saida_acima_do_saldo_e_bloqueada_com_400(self):
        resposta = self.registrar(quantidade=11)
        self.assertEqual(resposta.status_code, 400)
        self.assertIn("quantidade", resposta.json())
        self.produto.refresh_from_db()
        self.assertEqual(self.produto.quantidade, 10)
        self.assertEqual(MovimentacaoEstoque.objects.count(), 0)

    def test_motivo_incompativel_retorna_400(self):
        resposta = self.registrar(tipo="ENTRADA", motivo="VENDA")
        self.assertEqual(resposta.status_code, 400)
        self.assertIn("motivo", resposta.json())

    def test_quantidade_zero_retorna_400(self):
        resposta = self.registrar(quantidade=0)
        self.assertEqual(resposta.status_code, 400)

    def test_entrada_com_fornecedor(self):
        fornecedor = Fornecedor.objects.create(razao_social="Distribuidora X", cnpj="00.000.000/0001-00")
        resposta = self.registrar(tipo="ENTRADA", motivo="COMPRA", quantidade=5, fornecedor=fornecedor.pk)
        self.assertEqual(resposta.status_code, 201)
        self.assertEqual(resposta.json()["saldo_apos"], 15)

    def test_lista_historico_retorna_200(self):
        self.registrar()
        resposta = self.client.get(reverse("movimentacao-list"))
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(len(resposta.json()), 1)

    def test_nao_aceita_alteracao_nem_exclusao(self):
        self.registrar()
        movimentacao = MovimentacaoEstoque.objects.get()
        # Sem rota de detalhe: PUT/DELETE não existem para o log de auditoria.
        url = f"/api/movimentacoes/{movimentacao.pk}/"
        self.assertIn(self.client.put(url, data="{}", content_type="application/json").status_code, {404, 405})
        self.assertIn(self.client.delete(url).status_code, {404, 405})
        self.assertEqual(MovimentacaoEstoque.objects.count(), 1)


class FornecedorApiTests(ApiTestCase):
    def test_lista_fornecedores(self):
        Fornecedor.objects.create(razao_social="Distribuidora X", cnpj="00.000.000/0001-00")
        resposta = self.client.get(reverse("fornecedor-list"))
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.json()[0]["razao_social"], "Distribuidora X")


class CepApiTests(ApiTestCase):
    def test_cep_valido_retorna_endereco(self):
        corpo = json.dumps({"cep": "01001-000", "logradouro": "Praça da Sé", "bairro": "Sé",
                            "localidade": "São Paulo", "uf": "SP"})
        with mock.patch("estoque.cep.urlopen", return_value=FakeResposta(corpo)):
            resposta = self.client.get(reverse("api-cep", args=["01001-000"]))
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.json()["cidade"], "São Paulo")
        self.assertEqual(resposta.json()["uf"], "SP")

    def test_cep_inexistente_retorna_404(self):
        with mock.patch("estoque.cep.urlopen", return_value=FakeResposta('{"erro": true}')):
            resposta = self.client.get(reverse("api-cep", args=["99999999"]))
        self.assertEqual(resposta.status_code, 404)

    def test_cep_com_formato_invalido_retorna_400_sem_chamar_servico(self):
        with mock.patch("estoque.cep.urlopen") as chamada:
            resposta = self.client.get(reverse("api-cep", args=["123"]))
        self.assertEqual(resposta.status_code, 400)
        chamada.assert_not_called()

    def test_servico_fora_do_ar_retorna_503(self):
        with mock.patch("estoque.cep.urlopen", side_effect=TimeoutError):
            resposta = self.client.get(reverse("api-cep", args=["01001000"]))
        self.assertEqual(resposta.status_code, 503)


class PainelTests(ApiTestCase):
    def test_painel_responde_200_e_mostra_indicadores(self):
        self.produto.quantidade = 2  # abaixo do mínimo (4)
        self.produto.save()
        resposta = self.client.get(reverse("dashboard"))
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.context["indicadores"]["total_produtos"], 1)
        self.assertEqual(resposta.context["indicadores"]["produtos_criticos"], 1)
        self.assertEqual(resposta.context["indicadores"]["total_unidades"], 2)
        # custo do produto de teste é 20,00: capital = 2 x 20,00
        self.assertEqual(resposta.context["indicadores"]["capital_imobilizado"], Decimal("40.00"))

    def test_painel_envia_dados_dos_graficos(self):
        resposta = self.client.get(reverse("dashboard"))
        self.assertContains(resposta, 'id="dados-categorias"')
        self.assertContains(resposta, "Bebidas")
        labels = resposta.context["grafico_categorias"]["labels"]
        self.assertIn("Bebidas", labels)
        self.assertEqual(len(labels), len(resposta.context["grafico_categorias"]["valores"]))

    def test_painel_exige_login(self):
        self.client.logout()
        self.assertEqual(self.client.get(reverse("dashboard")).status_code, 302)


class PaginasWebTests(ApiTestCase):
    def test_paginas_exigem_login(self):
        self.client.logout()
        for nome in ["estoque-lista", "movimentar", "historico"]:
            with self.subTest(pagina=nome):
                resposta = self.client.get(reverse(nome))
                self.assertEqual(resposta.status_code, 302)
                self.assertIn("/contas/login/", resposta["Location"])

    def test_paginas_respondem_200_para_usuario_logado(self):
        for nome in ["estoque-lista", "movimentar", "historico"]:
            with self.subTest(pagina=nome):
                self.assertEqual(self.client.get(reverse(nome)).status_code, 200)

    def test_estoque_mostra_alerta_com_aria_live(self):
        self.produto.quantidade = 1
        self.produto.save()
        resposta = self.client.get(reverse("estoque-lista"))
        self.assertContains(resposta, 'aria-live="polite"')
        self.assertContains(resposta, "1 produto(s) abaixo do estoque mínimo.")

    def test_movimentar_envia_motivos_por_tipo_para_o_script(self):
        resposta = self.client.get(reverse("movimentar"))
        self.assertContains(resposta, 'id="motivos-por-tipo"')
        self.assertContains(resposta, "Refrigerante 2L")
        self.assertContains(resposta, 'name="csrfmiddlewaretoken"')
