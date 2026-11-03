/* Funções compartilhadas pelas telas do sistema. Expostas em window.Estoque. */
(function () {
  "use strict";

  window.Estoque = window.Estoque || {};

  /** Lê um cookie pelo nome (usado para pegar o token CSRF do Django). */
  window.Estoque.lerCookie = function (nome) {
    var prefixo = nome + "=";
    var partes = document.cookie ? document.cookie.split(";") : [];
    for (var i = 0; i < partes.length; i++) {
      var parte = partes[i].trim();
      if (parte.indexOf(prefixo) === 0) {
        return decodeURIComponent(parte.substring(prefixo.length));
      }
    }
    return "";
  };

  /** Formata um número como moeda brasileira, ex.: R$ 12,50. */
  window.Estoque.formatarMoeda = function (valor) {
    return Number(valor).toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
  };

  /** Transforma a resposta de erro da API em uma frase legível. */
  window.Estoque.extrairErro = function (dados, padrao) {
    if (!dados || typeof dados !== "object") {
      return padrao;
    }
    if (dados.detail) {
      return dados.detail;
    }
    var partes = Object.keys(dados).map(function (campo) {
      var valor = dados[campo];
      var texto = Array.isArray(valor) ? valor.join(" ") : String(valor);
      return campo === "non_field_errors" ? texto : campo + ": " + texto;
    });
    return partes.length ? partes.join(" ") : padrao;
  };

  /** Mostra uma mensagem em um elemento com aria-live, com tipo visual. */
  window.Estoque.mostrarMensagem = function (elemento, texto, tipo) {
    elemento.textContent = texto;
    elemento.className = "feedback" + (tipo ? " feedback-" + tipo : "");
  };
})();
