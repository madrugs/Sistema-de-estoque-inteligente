/* Gráficos do painel (Chart.js). Sem Chart.js, a página segue funcionando com os números. */
(function () {
  "use strict";

  var aviso = document.getElementById("aviso-graficos");

  if (typeof Chart === "undefined") {
    aviso.textContent = "Os gráficos não puderam ser carregados. Os indicadores e a tabela continuam disponíveis.";
    return;
  }

  function lerDados(id) {
    return JSON.parse(document.getElementById(id).textContent);
  }

  var cores = ["#1f5f3b", "#0b57d0", "#b06000", "#8a1c12", "#5b3e96"];

  var categorias = lerDados("dados-categorias");
  new Chart(document.getElementById("grafico-categorias"), {
    type: "bar",
    data: {
      labels: categorias.labels,
      datasets: [{
        label: "Unidades em estoque",
        data: categorias.valores,
        backgroundColor: cores[0],
      }],
    },
    options: {
      plugins: { legend: { display: false } },
      scales: { y: { beginAtZero: true, ticks: { precision: 0 } } },
    },
  });

  var movimentos = lerDados("dados-movimentos");
  new Chart(document.getElementById("grafico-movimentos"), {
    type: "doughnut",
    data: {
      labels: movimentos.labels,
      datasets: [{
        data: movimentos.valores,
        backgroundColor: [cores[1], cores[2]],
      }],
    },
  });
})();
