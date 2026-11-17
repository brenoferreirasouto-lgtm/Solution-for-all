// Página Exportar (entrega #8): o botão abre a janela de impressão, onde dá para salvar em PDF.
(function () {
  document.querySelectorAll("[data-imprimir]").forEach(function (botao) {
    botao.hidden = false;
    botao.addEventListener("click", function () {
      window.print();
    });
  });
})();
