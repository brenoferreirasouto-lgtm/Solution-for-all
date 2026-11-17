// Tela Adaptar material (entrega #7).
// - Mostra só o campo da forma de envio escolhida (arquivo, texto ou material já enviado).
// - Marca "Do perfil" nos formatos do aluno e escolhe o primeiro quando o aluno muda.
// - Evita clique duplo no Gerar.
// Sem JavaScript, todos os campos aparecem e o formulário funciona igual.
(function () {
  var form = document.querySelector("[data-adaptar]");
  if (!form) return;

  var paineis = form.querySelectorAll("[data-origem]");
  var origens = form.querySelectorAll('input[name="origem"]');

  function mostrarOrigem() {
    var marcada = form.querySelector('input[name="origem"]:checked');
    var valor = marcada ? marcada.value : "arquivo";
    paineis.forEach(function (painel) {
      painel.hidden = painel.dataset.origem.split(" ").indexOf(valor) === -1;
    });
  }
  origens.forEach(function (radio) {
    radio.addEventListener("change", mostrarOrigem);
  });
  mostrarOrigem();

  var aluno = form.querySelector('select[name="aluno"]');
  var formatos = form.querySelectorAll('input[name="tipo"]');

  function formatosDoAluno() {
    var opcao = aluno && aluno.options[aluno.selectedIndex];
    var lista = opcao && opcao.dataset.formatos ? opcao.dataset.formatos.split(",") : [];
    return lista.filter(Boolean);
  }

  function marcarPerfil(escolher) {
    var doPerfil = formatosDoAluno();
    formatos.forEach(function (radio) {
      var selo = radio.closest(".formato").querySelector("[data-perfil]");
      if (selo) selo.hidden = doPerfil.indexOf(radio.value) === -1;
      if (escolher && doPerfil.length) radio.checked = radio.value === doPerfil[0];
    });
  }
  if (aluno) {
    aluno.addEventListener("change", function () {
      marcarPerfil(true);
    });
  }
  marcarPerfil(false);

  var botao = form.querySelector("[data-gerar]");
  var rotulo = botao ? botao.textContent : "";
  form.addEventListener("submit", function () {
    if (!botao) return;
    botao.disabled = true;
    botao.textContent = "Gerando…";
  });
  // Ao voltar pelo navegador, o botão volta ao normal.
  window.addEventListener("pageshow", function () {
    if (!botao) return;
    botao.disabled = false;
    botao.textContent = rotulo;
  });
})();
