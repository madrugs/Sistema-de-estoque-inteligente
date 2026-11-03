/* Tela de movimentação: subtotal automático, saldo previsto e envio via fetch(). */
(function () {
  "use strict";

  var form = document.getElementById("form-movimentacao");
  if (!form) {
    return;
  }

  var produto = document.getElementById("produto");
  var tipo = document.getElementById("tipo");
  var motivo = document.getElementById("motivo");
  var quantidade = document.getElementById("quantidade");
  var fornecedor = document.getElementById("fornecedor");
  var observacao = document.getElementById("observacao");
  var feedback = document.getElementById("feedback");
  var botao = document.getElementById("botao-registrar");
  var saldoAtual = document.getElementById("saldo-atual");
  var saldoPrevisto = document.getElementById("saldo-previsto");
  var valorUnitario = document.getElementById("valor-unitario");
  var subtotal = document.getElementById("subtotal");
  var mapaMotivos = JSON.parse(document.getElementById("motivos-por-tipo").textContent);

  var Estoque = window.Estoque;

  function opcaoSelecionada() {
    return produto.options[produto.selectedIndex];
  }

  function ehEntrada() {
    return tipo.value === "ENTRADA";
  }

  /** Repõe as opções de motivo conforme o tipo escolhido. */
  function preencherMotivos() {
    var anterior = motivo.value;
    var opcoes = (mapaMotivos[tipo.value] || []).map(function (item) {
      var opcao = document.createElement("option");
      opcao.value = item[0];
      opcao.textContent = item[1];
      return opcao;
    });
    motivo.replaceChildren(...opcoes);
    motivo.selectedIndex = Math.max(0, opcoes.findIndex(function (opcao) {
      return opcao.value === anterior;
    }));
  }

  /** Recalcula saldo previsto e subtotal a cada mudança no formulário. */
  function atualizarResumo() {
    var op = opcaoSelecionada();
    var qtd = parseInt(quantidade.value, 10);
    if (!op || !op.value || isNaN(qtd) || qtd < 0) {
      saldoAtual.textContent = "–";
      saldoPrevisto.textContent = "–";
      valorUnitario.textContent = "–";
      subtotal.textContent = "–";
      return;
    }

    var saldo = parseInt(op.dataset.saldo, 10);
    var unitario = Number(ehEntrada() ? op.dataset.custo : op.dataset.venda);
    var previsto = ehEntrada() ? saldo + qtd : saldo - qtd;

    saldoAtual.textContent = saldo;
    saldoPrevisto.textContent = previsto < 0 ? "Saldo insuficiente" : previsto;
    valorUnitario.textContent = Estoque.formatarMoeda(unitario);
    subtotal.textContent = Estoque.formatarMoeda(unitario * qtd);
  }

  /** Validações feitas antes do envio (o servidor valida de novo). */
  function validarAntesDeEnviar() {
    var op = opcaoSelecionada();
    if (!op || !op.value) {
      return { campo: produto, texto: "Selecione um produto." };
    }
    var qtd = parseInt(quantidade.value, 10);
    if (!Number.isInteger(qtd) || qtd < 1) {
      return { campo: quantidade, texto: "A quantidade deve ser um número inteiro maior que zero." };
    }
    if (!ehEntrada() && qtd > parseInt(op.dataset.saldo, 10)) {
      return {
        campo: quantidade,
        texto: "Saída bloqueada: quantidade maior que o saldo em estoque (" + op.dataset.saldo + ").",
      };
    }
    return null;
  }

  function registrar(evento) {
    evento.preventDefault();

    var erro = validarAntesDeEnviar();
    if (erro) {
      Estoque.mostrarMensagem(feedback, erro.texto, "erro");
      erro.campo.focus();
      return;
    }

    var op = opcaoSelecionada();
    var corpo = {
      produto: Number(op.value),
      tipo: tipo.value,
      motivo: motivo.value,
      quantidade: parseInt(quantidade.value, 10),
      observacao: observacao.value,
      fornecedor: fornecedor.value ? Number(fornecedor.value) : null,
    };

    botao.disabled = true;
    Estoque.mostrarMensagem(feedback, "Registrando movimentação…", "");

    fetch("/api/movimentacoes/", {
      method: "POST",
      credentials: "same-origin",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
        "X-CSRFToken": Estoque.lerCookie("csrftoken"),
      },
      body: JSON.stringify(corpo),
    })
      .then(function (resposta) {
        return resposta.json().then(function (dados) {
          return { ok: resposta.ok, dados: dados };
        });
      })
      .then(function (resultado) {
        if (!resultado.ok) {
          throw resultado.dados;
        }
        var novoSaldo = resultado.dados.saldo_apos;
        op.dataset.saldo = novoSaldo;
        Estoque.mostrarMensagem(
          feedback,
          "Movimentação registrada. Novo saldo de " + op.textContent.trim() + ": " + novoSaldo + ".",
          "ok"
        );
        quantidade.value = 1;
        observacao.value = "";
        atualizarResumo();
      })
      .catch(function (erroRecebido) {
        var texto = Estoque.extrairErro(
          erroRecebido,
          "Não foi possível registrar. Verifique a conexão e tente novamente."
        );
        Estoque.mostrarMensagem(feedback, texto, "erro");
      })
      .finally(function () {
        botao.disabled = false;
      });
  }

  tipo.addEventListener("change", function () {
    preencherMotivos();
    atualizarResumo();
  });
  produto.addEventListener("change", atualizarResumo);
  quantidade.addEventListener("input", atualizarResumo);
  form.addEventListener("submit", registrar);

  preencherMotivos();
  atualizarResumo();
})();
