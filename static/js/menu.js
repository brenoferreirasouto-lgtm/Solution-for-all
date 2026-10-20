// Abre e fecha o menu ☰ no celular. No desktop o menu é a barra lateral fixa.
(function () {
  var abrir = document.querySelector("[data-menu-abrir]");
  var menu = document.getElementById("menu");
  if (!abrir || !menu) return;

  var corpo = document.body;
  var fundo = document.querySelector(".menu-fundo");

  function definir(aberto) {
    corpo.classList.toggle("menu-aberto", aberto);
    abrir.setAttribute("aria-expanded", String(aberto));
    if (fundo) fundo.hidden = !aberto;
    if (aberto) {
      var primeiro = menu.querySelector("a, button");
      if (primeiro) primeiro.focus();
    } else {
      abrir.focus();
    }
  }

  abrir.addEventListener("click", function () {
    definir(!corpo.classList.contains("menu-aberto"));
  });

  document.querySelectorAll("[data-menu-fechar]").forEach(function (el) {
    el.addEventListener("click", function () {
      definir(false);
    });
  });

  document.addEventListener("keydown", function (evento) {
    if (evento.key === "Escape" && corpo.classList.contains("menu-aberto")) definir(false);
  });
})();
