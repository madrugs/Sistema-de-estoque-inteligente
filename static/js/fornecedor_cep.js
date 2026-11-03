/* Cadastro de fornecedor (Django admin): preenche o endereço a partir do CEP. */
(function () {
  "use strict";

  var cep = document.getElementById("id_cep");
  if (!cep) {
    return;
  }

  var campos = {
    logradouro: document.getElementById("id_logradouro"),
    bairro: document.getElementById("id_bairro"),
    cidade: document.getElementById("id_cidade"),
    uf: document.getElementById("id_uf"),
  };

  var status = document.createElement("p");
  status.className = "help";
  status.setAttribute("aria-live", "polite");
  cep.insertAdjacentElement("afterend", status);

  function consultarCep() {
    var digitos = cep.value.replace(/\D/g, "");
    if (digitos.length !== 8) {
      return;
    }

    status.textContent = "Consultando CEP…";
    fetch("/api/cep/" + digitos + "/", {
      credentials: "same-origin",
      headers: { Accept: "application/json" },
    })
      .then(function (resposta) {
        return resposta.json().then(function (dados) {
          return { ok: resposta.ok, dados: dados };
        });
      })
      .then(function (resultado) {
        if (!resultado.ok) {
          throw new Error(resultado.dados.detail || "Não foi possível consultar o CEP.");
        }
        Object.keys(campos).forEach(function (nome) {
          if (campos[nome] && resultado.dados[nome]) {
            campos[nome].value = resultado.dados[nome];
          }
        });
        status.textContent = "Endereço preenchido a partir do CEP.";
      })
      .catch(function (erro) {
        status.textContent = erro.message || "Não foi possível consultar o CEP.";
      });
  }

  cep.addEventListener("blur", consultarCep);
})();
