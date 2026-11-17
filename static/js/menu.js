// Menu ☰ no celular (gaveta) e busca de alunos no menu. No desktop o menu é a barra lateral fixa.
(function () {
  var abrir = document.querySelector("[data-menu-abrir]");
  var abrirBusca = document.querySelector("[data-menu-abrir-busca]");
  var menu = document.getElementById("menu");
  if (!abrir || !menu) return;

  var corpo = document.body;
  var fundo = document.querySelector(".menu-fundo");
  var entradaBusca = menu.querySelector("[data-busca-entrada]");

  // "origem" é o botão que abriu o menu: o foco volta para ele ao fechar.
  function definir(aberto, origem) {
    corpo.classList.toggle("menu-aberto", aberto);
    abrir.setAttribute("aria-expanded", String(aberto));
    if (fundo) fundo.hidden = !aberto;
    if (aberto) {
      var inicio = origem === abrirBusca && entradaBusca ? entradaBusca : menu.querySelector("a, button");
      menu._origem = origem || abrir;
      // A gaveta começa invisível (visibility: hidden) e o navegador não deixa focar
      // um elemento invisível. Espera ela aparecer, ou o foco se perde.
      if (inicio) window.setTimeout(function () { inicio.focus(); }, 60);
    } else {
      (menu._origem || abrir).focus();
    }
  }

  abrir.addEventListener("click", function () {
    definir(!corpo.classList.contains("menu-aberto"), abrir);
  });

  // A lupa do topo abre o menu já com o cursor na busca.
  if (abrirBusca) {
    abrirBusca.addEventListener("click", function () {
      definir(true, abrirBusca);
    });
  }

  document.querySelectorAll("[data-menu-fechar]").forEach(function (el) {
    el.addEventListener("click", function () {
      definir(false);
    });
  });

  document.addEventListener("keydown", function (evento) {
    if (evento.key === "Escape" && corpo.classList.contains("menu-aberto")) definir(false);
  });
})();

// Filtra a lista de alunos do menu enquanto a pessoa digita. Ignora acentos e
// maiúsculas, e cada palavra digitada precisa aparecer no nome ou na turma.
// Sem JavaScript, o Enter envia o formulário para /alunos/?q=.
(function () {
  var secao = document.querySelector("[data-busca-menu]");
  if (!secao) return;

  var entrada = secao.querySelector("[data-busca-entrada]");
  var lista = secao.querySelector("[data-busca-lista]");
  var vazio = secao.querySelector("[data-busca-vazio]");
  var status = secao.querySelector("[data-busca-status]");
  if (!entrada || !lista) return;

  var itens = Array.prototype.slice.call(lista.querySelectorAll("li"));

  function normalizar(texto) {
    return (texto || "")
      .normalize("NFD")
      .replace(/[̀-ͯ]/g, "")
      .toLowerCase()
      .split(/\s+/)
      .filter(Boolean)
      .join(" ");
  }

  var textos = itens.map(function (li) {
    return normalizar(li.getAttribute("data-busca-texto"));
  });

  function filtrar() {
    var palavras = normalizar(entrada.value).split(" ").filter(Boolean);
    var visiveis = 0;
    itens.forEach(function (li, i) {
      var combina = palavras.every(function (p) {
        return textos[i].indexOf(p) !== -1;
      });
      li.hidden = !combina;
      if (combina) visiveis += 1;
    });
    if (vazio) vazio.hidden = visiveis !== 0;
    if (status) {
      status.textContent = palavras.length
        ? visiveis === 0
          ? "Nenhum aluno encontrado."
          : visiveis + (visiveis === 1 ? " aluno encontrado." : " alunos encontrados.")
        : "";
    }
  }

  entrada.addEventListener("input", filtrar);
  // O X do campo de busca (type="search") também dispara "search".
  entrada.addEventListener("search", filtrar);
})();
