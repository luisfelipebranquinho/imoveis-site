// Filtros da vitrine, galeria de fotos e "ler descrição completa". Sem dependências.
(function () {
  "use strict";

  // ---------- Vitrine: filtros e paginação ----------
  // A primeira página vem pronta no HTML; a lista completa é lida de dados/vitrine.json.
  var form = document.getElementById("filtros");
  var grade = document.getElementById("grade");
  if (form && grade) {
    var contagem = document.getElementById("contagem");
    var semResultado = document.getElementById("sem-resultado");
    var botaoMais = document.getElementById("mostrar-mais");
    var porPagina = Number(grade.getAttribute("data-por-pagina")) || 24;
    var icones = {};
    document.querySelectorAll("#icones")[0].content.querySelectorAll("[data-icone]").forEach(function (s) {
      icones[s.getAttribute("data-icone")] = s.innerHTML;
    });
    var todos = null, lista = [], mostrados = 0, carregando = null;

    function carregar() {
      if (!carregando) {
        carregando = fetch(grade.getAttribute("data-dados"))
          .then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); })
          .then(function (d) { todos = d; return d; });
      }
      return carregando;
    }
    function esc(s) {
      return String(s == null ? "" : s).replace(/[&<>"]/g, function (c) {
        return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c];
      });
    }
    function brl(v) { return v ? "R$ " + Math.round(v).toLocaleString("pt-BR") : "Valor sob consulta"; }
    function plural(n, um, varios) { return n + " " + (n === 1 ? um : varios); }
    function area(n) { return String(n).replace(".", ",") + " m²"; }
    function fato(nome, texto) { return "<li>" + icones[nome] + "<span>" + esc(texto) + "</span></li>"; }
    function cartao(p) {
      var fatos = (p.a ? fato("area", area(p.a)) : "") +
        (p.q != null ? fato("quartos", plural(p.q, "quarto", "quartos")) : "") +
        (p.bh != null ? fato("banheiros", plural(p.bh, "banheiro", "banheiros")) : "") +
        (p.v != null ? fato("vagas", plural(p.v, "vaga", "vagas")) : "");
      var selos = (p.d ? '<span class="selo">Destaque</span>' : "") + (p.l ? '<span class="selo selo-claro">Lançamento</span>' : "");
      var img = p.f ? '<img src="' + esc(p.f) + '" alt="" loading="lazy" decoding="async" referrerpolicy="no-referrer">'
        : '<span class="sem-foto">Fotos em breve</span>';
      return '<article class="card"><a class="card-link" href="imovel/' + encodeURIComponent(p.c) + '/">' +
        '<div class="card-foto">' + img + '<div class="selos">' + selos + "</div></div>" +
        '<div class="card-corpo"><p class="card-local">' + esc(p.b) + ", " + esc(p.ci) + "</p>" +
        '<h3 class="card-titulo">' + esc(p.tr) + (p.a ? " com " + area(p.a) : "") + "</h3>" +
        '<p class="card-preco">' + brl(p.p) + '</p><ul class="fatos">' + fatos + "</ul></div></a></article>";
    }
    function filtros() {
      var f = {};
      Array.prototype.forEach.call(form.elements, function (el) { if (el.name) f[el.name] = el.value; });
      return f;
    }
    function mostrarMais() {
      var html = lista.slice(mostrados, mostrados + porPagina).map(cartao).join("");
      grade.insertAdjacentHTML("beforeend", html);
      mostrados = Math.min(lista.length, mostrados + porPagina);
      botaoMais.hidden = mostrados >= lista.length;
    }
    function aplicar() {
      var f = filtros();
      lista = todos.filter(function (p) {
        return (!f.tipo || p.t === f.tipo) && (!f.bairro || p.b === f.bairro) &&
          (!f.preco || (p.p > 0 && p.p <= Number(f.preco))) &&
          (!f.quartos || (p.q || 0) >= Number(f.quartos));
      });
      if (f.ordem === "menor") lista.sort(function (a, b) { return (a.p || Infinity) - (b.p || Infinity); });
      if (f.ordem === "maior") lista.sort(function (a, b) { return b.p - a.p; });
      if (f.ordem === "area") lista.sort(function (a, b) { return b.a - a.a; });
      grade.innerHTML = "";
      mostrados = 0;
      mostrarMais();
      contagem.textContent = plural(lista.length, "imóvel", "imóveis");
      semResultado.hidden = lista.length !== 0;

      var q = new URLSearchParams();
      Object.keys(f).forEach(function (k) { if (f[k]) q.set(k, f[k]); });
      history.replaceState(null, "", location.pathname + (q.toString() ? "?" + q : "") + location.hash);
    }
    function aoMudar() {
      contagem.textContent = "Carregando…";
      carregar().then(aplicar).catch(function () {
        contagem.textContent = "Não foi possível carregar a lista. Recarregue a página.";
      });
    }

    var params = new URLSearchParams(location.search);
    Array.prototype.forEach.call(form.elements, function (el) {
      if (el.name && params.get(el.name)) el.value = params.get(el.name);
    });
    form.addEventListener("change", aoMudar);
    form.addEventListener("submit", function (ev) { ev.preventDefault(); });
    botaoMais.addEventListener("click", function () {
      botaoMais.disabled = true;
      carregar().then(function () {
        if (!lista.length && !mostrados) { lista = todos; mostrados = grade.children.length; }
        mostrarMais();
      }).finally(function () { botaoMais.disabled = false; });
    });
    var limpar = document.getElementById("limpar");
    if (limpar) limpar.addEventListener("click", function () { form.reset(); aoMudar(); });
    if (params.toString()) aoMudar();
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
