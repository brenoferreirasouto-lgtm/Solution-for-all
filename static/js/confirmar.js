// Formulários com data-confirmar="pergunta" pedem confirmação antes de enviar
// (ex.: arquivar aluno, excluir horário). Sem JavaScript, enviam direto.
document.addEventListener("submit", function (evento) {
  var pergunta = evento.target.getAttribute("data-confirmar");
  if (pergunta && !window.confirm(pergunta)) {
    evento.preventDefault();
  }
});
