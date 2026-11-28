// Formulários com data-confirmar="pergunta" pedem confirmação antes de enviar
// (ex.: arquivar aluno, excluir horário). Sem JavaScript, enviam direto.
// Formulários com data-aguarde="Gerando…" travam o botão enquanto a IA responde,
// para evitar clique duplo (cada clique gastaria o limite gratuito da IA).
document.addEventListener("submit", function (evento) {
  var form = evento.target;
  var pergunta = form.getAttribute("data-confirmar");
  if (pergunta && !window.confirm(pergunta)) {
    evento.preventDefault();
    return;
  }
  var aguarde = form.getAttribute("data-aguarde");
  var botao = aguarde && form.querySelector("button[type=submit]");
  if (botao) {
    botao.setAttribute("data-rotulo", botao.textContent);
    botao.disabled = true;
    botao.textContent = aguarde;
  }
});
// Ao voltar pelo navegador, os botões travados voltam ao normal.
window.addEventListener("pageshow", function () {
  document.querySelectorAll("button[data-rotulo]").forEach(function (botao) {
    botao.disabled = false;
    botao.textContent = botao.getAttribute("data-rotulo");
    botao.removeAttribute("data-rotulo");
  });
});
