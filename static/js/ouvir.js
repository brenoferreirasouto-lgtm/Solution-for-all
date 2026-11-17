// Botão Ouvir do material adaptado (entrega #8).
// Usa a voz do próprio navegador (Web Speech API), sem custo e sem servidor.
// Só usa vozes em português instaladas no aparelho (localService): assim o texto
// não sai do computador. Sem uma voz dessas, o botão não aparece.
(function () {
  var botao = document.querySelector("[data-ouvir]");
  var fonte = document.querySelector("[data-ouvir-fonte]");
  if (!botao || !fonte || !("speechSynthesis" in window) || !window.SpeechSynthesisUtterance) return;

  var fala = window.speechSynthesis;

  function vozLocal() {
    var locais = fala.getVoices().filter(function (v) {
      return v.localService && /^pt/i.test(v.lang);
    });
    var brasil = locais.filter(function (v) {
      return /pt[-_]BR/i.test(v.lang);
    });
    return brasil[0] || locais[0] || null;
  }

  function atualizar() {
    botao.hidden = !vozLocal();
  }
  atualizar();
  // As vozes chegam depois do carregamento em alguns navegadores.
  if (fala.addEventListener) fala.addEventListener("voiceschanged", atualizar);

  function texto() {
    return ("value" in fonte ? fonte.value : fonte.innerText) || "";
  }

  function parar() {
    fala.cancel();
    botao.textContent = "Ouvir";
    botao.setAttribute("aria-pressed", "false");
  }

  botao.addEventListener("click", function () {
    if (fala.speaking || fala.pending) {
      parar();
      return;
    }
    var voz = vozLocal();
    // Um trecho por parágrafo: textos longos de uma vez são cortados em alguns navegadores.
    var trechos = texto()
      .split(/\n+/)
      .map(function (t) {
        return t.trim();
      })
      .filter(Boolean);
    if (!voz || !trechos.length) return;

    trechos.forEach(function (trecho, indice) {
      var frase = new SpeechSynthesisUtterance(trecho);
      frase.voice = voz;
      frase.lang = voz.lang;
      frase.rate = 0.95;
      if (indice === trechos.length - 1) frase.onend = parar;
      frase.onerror = parar;
      fala.speak(frase);
    });
    botao.textContent = "Parar";
    botao.setAttribute("aria-pressed", "true");
  });

  window.addEventListener("pagehide", function () {
    fala.cancel();
  });
})();
