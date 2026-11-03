/* Busca e filtro em tempo real da tabela de estoque (evento `input`). */
(function () {
  "use strict";

  var busca = document.getElementById("busca");
  var somenteCriticos = document.getElementById("somente-criticos");
  var contagem = document.getElementById("contagem");
  var linhas = Array.prototype.slice.call(
    document.querySelectorAll("#tabela-estoque tbody tr[data-nome]")
  );

  if (!busca || !somenteCriticos) {
    return;
  }

  function filtrar() {
    var termo = busca.value.trim().toLowerCase();
    var apenasCriticos = somenteCriticos.checked;
    var exibidas = 0;

    linhas.forEach(function (linha) {
      var combina =
        !termo ||
        linha.dataset.nome.indexOf(termo) !== -1 ||
        linha.dataset.codigo.indexOf(termo) !== -1;
      var mostrar = combina && (!apenasCriticos || linha.dataset.critico === "1");

      linha.hidden = !mostrar;
      if (mostrar) {
        exibidas += 1;
      }
    });

    contagem.textContent = exibidas + " produto(s) exibido(s).";
  }

  busca.addEventListener("input", filtrar);
  somenteCriticos.addEventListener("change", filtrar);
})();
