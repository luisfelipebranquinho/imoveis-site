// Filtros da vitrine, galeria de fotos e "ler descrição completa". Sem dependências.
(function () {
  "use strict";

  // ---------- Filtros da página inicial ----------
  var form = document.getElementById("filtros");
  var grade = document.getElementById("grade");
  if (form && grade) {
    var cards = Array.prototype.slice.call(grade.querySelectorAll(".card"));
    var contagem = document.getElementById("contagem");
    var semResultado = document.getElementById("sem-resultado");

    var params = new URLSearchParams(location.search);
    Array.prototype.forEach.call(form.elements, function (el) {
      if (el.name && params.get(el.name)) el.value = params.get(el.name);
    });

    function aplicar() {
      var f = {};
      Array.prototype.forEach.call(form.elements, function (el) { if (el.name) f[el.name] = el.value; });
      var visiveis = 0;
      cards.forEach(function (c) {
        var d = c.dataset;
        var ok = (!f.tipo || d.tipo === f.tipo) &&
          (!f.bairro || d.bairro === f.bairro) &&
          (!f.preco || (Number(d.preco) > 0 && Number(d.preco) <= Number(f.preco))) &&
          (!f.quartos || Number(d.quartos) >= Number(f.quartos));
        c.hidden = !ok;
        if (ok) visiveis++;
      });
      var ordem = cards.slice().sort(function (a, b) {
        var x = a.dataset, y = b.dataset;
        if (f.ordem === "menor") return (Number(x.preco) || Infinity) - (Number(y.preco) || Infinity);
        if (f.ordem === "maior") return Number(y.preco) - Number(x.preco);
        if (f.ordem === "area") return Number(y.area) - Number(x.area);
        return Number(x.ordem) - Number(y.ordem);
      });
      ordem.forEach(function (c) { grade.appendChild(c); });
      contagem.textContent = visiveis + (visiveis === 1 ? " imóvel" : " imóveis");
      semResultado.hidden = visiveis !== 0 || cards.length === 0;

      var q = new URLSearchParams();
      Object.keys(f).forEach(function (k) { if (f[k]) q.set(k, f[k]); });
      var nova = location.pathname + (q.toString() ? "?" + q : "") + location.hash;
      history.replaceState(null, "", nova);
    }

    form.addEventListener("change", aplicar);
    form.addEventListener("submit", function (ev) { ev.preventDefault(); });
    var limpar = document.getElementById("limpar");
    if (limpar) limpar.addEventListener("click", function () { form.reset(); aplicar(); });
    if (params.toString()) aplicar();
  }

  // ---------- Descrição longa ----------
  var desc = document.getElementById("descricao");
  var lerMais = document.getElementById("ler-mais");
  if (desc && lerMais && desc.scrollHeight > 340) {
    desc.classList.add("recolhida");
    lerMais.hidden = false;
    lerMais.addEventListener("click", function () {
      var aberta = desc.classList.toggle("recolhida") === false;
      lerMais.setAttribute("aria-expanded", String(aberta));
      lerMais.textContent = aberta ? "Mostrar menos" : "Ler descrição completa";
    });
  }

  // ---------- Galeria ----------
  var galeria = document.getElementById("galeria");
  if (!galeria) return;
  var fotos = JSON.parse(galeria.getAttribute("data-fotos") || "[]");
  if (!fotos.length) return;
  var img = galeria.querySelector("img");
  var legenda = galeria.querySelector("figcaption");
  var atual = 0, origem = null, toqueX = null;

  function mostrar(i) {
    atual = (i + fotos.length) % fotos.length;
    img.src = fotos[atual];
    legenda.textContent = "Foto " + (atual + 1) + " de " + fotos.length;
    new Image().src = fotos[(atual + 1) % fotos.length];
  }
  function abrir(i, botao) {
    origem = botao;
    galeria.hidden = false;
    document.body.style.overflow = "hidden";
    mostrar(i);
    galeria.querySelector(".galeria-fechar").focus();
  }
  function fechar() {
    galeria.hidden = true;
    document.body.style.overflow = "";
    if (origem) origem.focus();
  }

  document.querySelectorAll("[data-foto]").forEach(function (b) {
    b.addEventListener("click", function () { abrir(Number(b.getAttribute("data-foto")), b); });
  });
  galeria.querySelector(".galeria-fechar").addEventListener("click", fechar);
  galeria.querySelector(".galeria-ant").addEventListener("click", function () { mostrar(atual - 1); });
  galeria.querySelector(".galeria-prox").addEventListener("click", function () { mostrar(atual + 1); });
  galeria.addEventListener("click", function (ev) { if (ev.target === galeria) fechar(); });
  document.addEventListener("keydown", function (ev) {
    if (galeria.hidden) return;
    if (ev.key === "Escape") fechar();
    if (ev.key === "ArrowLeft") mostrar(atual - 1);
    if (ev.key === "ArrowRight") mostrar(atual + 1);
    if (ev.key === "Tab") {
      var focaveis = galeria.querySelectorAll("button");
      var primeiro = focaveis[0], ultimo = focaveis[focaveis.length - 1];
      if (ev.shiftKey && document.activeElement === primeiro) { ev.preventDefault(); ultimo.focus(); }
      else if (!ev.shiftKey && document.activeElement === ultimo) { ev.preventDefault(); primeiro.focus(); }
    }
  });
  galeria.addEventListener("touchstart", function (ev) { toqueX = ev.touches[0].clientX; }, { passive: true });
  galeria.addEventListener("touchend", function (ev) {
    if (toqueX === null) return;
    var dx = ev.changedTouches[0].clientX - toqueX;
    if (Math.abs(dx) > 40) mostrar(atual + (dx < 0 ? 1 : -1));
    toqueX = null;
  });
})();
