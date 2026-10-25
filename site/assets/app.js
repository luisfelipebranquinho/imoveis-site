// Busca, filtros e paginação da vitrine, carrosséis, galeria de fotos e contato pelo WhatsApp.
(function () {
  "use strict";
  var $ = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };
  function sem(s) { return String(s || "").normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase().trim(); }
  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"]/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c];
    });
  }

  // ---------- Carrosséis ----------
  $$("[data-rolar]").forEach(function (b) {
    b.addEventListener("click", function () {
      var alvo = document.getElementById(b.getAttribute("data-rolar"));
      alvo.scrollBy({ left: Number(b.getAttribute("data-dir")) * alvo.clientWidth * 0.9, behavior: "smooth" });
    });
  });

  // ---------- Vitrine ----------
  var filtros = $("#filtros");
  var grade = $("#grade");
  var busca = $("#busca");
  if (filtros && grade) {
    var contagem = $("#contagem"), semResultado = $("#sem-resultado"), botaoMais = $("#mostrar-mais");
    var avisoBusca = $("#busca-ativa");
    var porPagina = Number(grade.getAttribute("data-por-pagina")) || 24;
    var icones = {};
    $$("[data-icone]", $("#icones").content).forEach(function (s) { icones[s.getAttribute("data-icone")] = s.innerHTML; });
    var todos = null, lista = [], mostrados = 0, carregando = null;

    var carregar = function () {
      if (!carregando) {
        carregando = fetch(grade.getAttribute("data-dados"))
          .then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); })
          .then(function (d) { todos = d; return d; });
      }
      return carregando;
    };
    var brl = function (v) { return v ? "R$ " + Math.round(v).toLocaleString("pt-BR") : "Valor sob consulta"; };
    var plural = function (n, um, varios) { return n + " " + (n === 1 ? um : varios); };
    var area = function (n) { return String(n).replace(".", ",") + " m²"; };
    var fato = function (nome, rotulo, texto) {
      return '<li title="' + rotulo + '">' + icones[nome] + '<span><span class="sr">' + rotulo + ": </span>" + esc(texto) + "</span></li>";
    };
    var cartao = function (p) {
      var fatos = (p.a ? fato("area", "Área", area(p.a)) : "") +
        (p.q != null ? fato("quartos", "Quartos", p.q) : "") + (p.v != null ? fato("vagas", "Vagas", p.v) : "");
      var selos = (p.d ? '<span class="selo">Destaque</span>' : "") + (p.l ? '<span class="selo">Lançamento</span>' : "");
      var img = p.f ? '<img src="' + esc(p.f) + '" alt="" loading="lazy" decoding="async" referrerpolicy="no-referrer">'
        : '<span class="sem-foto">Fotos em breve</span>';
      return '<article class="card"><a class="card-link" href="imovel/' + encodeURIComponent(p.c) + '/">' +
        '<div class="card-foto">' + img + '<span class="pilula">' + esc(p.b) + '</span><span class="etiqueta">' + esc(p.tr) + "</span>" +
        (selos ? '<div class="selos">' + selos + "</div>" : "") + "</div>" +
        '<div class="card-corpo"><h3 class="card-titulo">' + esc(p.tr) + "</h3>" +
        '<p class="card-local">' + esc(p.b) + ", " + esc(p.ci) + " - " + esc(p.u) + "</p>" +
        '<p class="card-preco">' + brl(p.p) + '</p><ul class="fatos">' + fatos + "</ul></div></a></article>";
    };
    var valores = function () {
      var f = {};
      $$("[name]", filtros).forEach(function (el) { f[el.name] = el.value; });
      return f;
    };
    var mostrarMais = function () {
      grade.insertAdjacentHTML("beforeend", lista.slice(mostrados, mostrados + porPagina).map(cartao).join(""));
      mostrados = Math.min(lista.length, mostrados + porPagina);
      botaoMais.hidden = mostrados >= lista.length;
    };
    var aplicar = function () {
      var f = valores(), q = sem(f.q);
      lista = todos.filter(function (p) {
        return (!f.tipo || p.t === f.tipo) && (!f.regiao || p.r === f.regiao) &&
          (!f.preco || (p.p > 0 && p.p <= Number(f.preco))) && (!f.quartos || (p.q || 0) >= Number(f.quartos)) &&
          (!q || p.c === f.q.trim() || sem(p.b).indexOf(q) >= 0 || sem(p.ci).indexOf(q) >= 0 || sem(p.r).indexOf(q) >= 0);
      });
      if (f.ordem === "menor") lista.sort(function (a, b) { return (a.p || Infinity) - (b.p || Infinity); });
      if (f.ordem === "maior") lista.sort(function (a, b) { return b.p - a.p; });
      if (f.ordem === "area") lista.sort(function (a, b) { return b.a - a.a; });
      grade.innerHTML = "";
      mostrados = 0;
      mostrarMais();
      contagem.textContent = plural(lista.length, "imóvel", "imóveis");
      semResultado.hidden = lista.length !== 0;
      avisoBusca.hidden = !f.q;
      if (f.q) avisoBusca.innerHTML = "Resultados para “" + esc(f.q) + "”. <button type=\"button\" class=\"link\" id=\"limpar-busca\">Limpar busca</button>";
      var u = new URLSearchParams();
      Object.keys(f).forEach(function (k) { if (f[k]) u.set(k, f[k]); });
      history.replaceState(null, "", location.pathname + (u.toString() ? "?" + u : "") + location.hash);
    };
    var atualizar = function () {
      contagem.textContent = "Carregando…";
      return carregar().then(aplicar).catch(function () {
        contagem.textContent = "Não foi possível carregar a lista. Recarregue a página.";
      });
    };

    // Valores vindos do endereço (?regiao=..., ?q=...)
    var params = new URLSearchParams(location.search);
    $$("[name]", filtros).forEach(function (el) { if (params.get(el.name)) el.value = params.get(el.name); });
    if (busca) $$("[name]", busca).forEach(function (el) { if (params.get(el.name)) el.value = params.get(el.name); });

    filtros.addEventListener("change", atualizar);
    filtros.addEventListener("submit", function (ev) { ev.preventDefault(); });
    if (busca) {
      busca.addEventListener("submit", function (ev) {
        ev.preventDefault();
        $$("[name]", busca).forEach(function (el) {
          var alvo = filtros.querySelector('[name="' + el.name + '"]');
          if (alvo) alvo.value = el.value;
        });
        atualizar().then(function () { document.getElementById("imoveis").scrollIntoView(); });
      });
    }
    avisoBusca.addEventListener("click", function (ev) {
      if (ev.target.id !== "limpar-busca") return;
      filtros.querySelector('[name="q"]').value = "";
      if (busca) busca.querySelector('[name="q"]').value = "";
      atualizar();
    });
    botaoMais.addEventListener("click", function () {
      botaoMais.disabled = true;
      carregar().then(function () {
        if (!lista.length && !mostrados) { lista = todos; mostrados = grade.children.length; }
        mostrarMais();
      }).finally(function () { botaoMais.disabled = false; });
    });
    var limpar = $("#limpar");
    if (limpar) limpar.addEventListener("click", function () {
      filtros.reset();
      $$("[name]", filtros).forEach(function (el) { el.value = ""; });
      if (busca) busca.reset();
      atualizar();
    });
    if (params.toString()) atualizar();
  }

  // ---------- Contato pelo WhatsApp (página do imóvel) ----------
  var form = $("#form-whats");
  if (form) {
    form.addEventListener("submit", function (ev) {
      ev.preventDefault();
      var nome = form.nome.value.trim();
      var texto = (nome ? "Olá, meu nome é " + nome + ". " : "") + form.text.value.trim();
      window.open("https://wa.me/" + form.getAttribute("data-numero") + "?text=" + encodeURIComponent(texto), "_blank", "noopener");
    });
  }

  // ---------- Descrição longa ----------
  var desc = $("#descricao"), lerMais = $("#ler-mais");
  if (desc && lerMais && desc.scrollHeight > 360) {
    desc.classList.add("recolhida");
    lerMais.hidden = false;
    lerMais.addEventListener("click", function () {
      var aberta = desc.classList.toggle("recolhida") === false;
      lerMais.setAttribute("aria-expanded", String(aberta));
      lerMais.textContent = aberta ? "Mostrar menos" : "Ler descrição completa";
    });
  }

  // ---------- Galeria ----------
  var galeria = $("#galeria");
  if (!galeria) return;
  var fotos = JSON.parse(galeria.getAttribute("data-fotos") || "[]");
  if (!fotos.length) return;
  var img = $("img", galeria), legenda = $("figcaption", galeria), principal = $("#foto-principal");
  var atual = 0, naPrincipal = 0, origem = null, toqueX = null;

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
    $(".galeria-fechar", galeria).focus();
  }
  function fechar() {
    galeria.hidden = true;
    document.body.style.overflow = "";
    if (origem) origem.focus();
  }
  $$("[data-foto]").forEach(function (b) {
    b.addEventListener("click", function () {
      var i = b.classList.contains("principal-foto") ? naPrincipal : Number(b.getAttribute("data-foto"));
      abrir(i, b);
    });
  });
  $$("[data-passo]").forEach(function (b) {
    b.addEventListener("click", function () {
      naPrincipal = (naPrincipal + Number(b.getAttribute("data-passo")) + fotos.length) % fotos.length;
      principal.src = fotos[naPrincipal];
    });
  });
  $(".galeria-fechar", galeria).addEventListener("click", fechar);
  $(".galeria-ant", galeria).addEventListener("click", function () { mostrar(atual - 1); });
  $(".galeria-prox", galeria).addEventListener("click", function () { mostrar(atual + 1); });
  galeria.addEventListener("click", function (ev) { if (ev.target === galeria) fechar(); });
  document.addEventListener("keydown", function (ev) {
    if (galeria.hidden) return;
    if (ev.key === "Escape") fechar();
    if (ev.key === "ArrowLeft") mostrar(atual - 1);
    if (ev.key === "ArrowRight") mostrar(atual + 1);
    if (ev.key === "Tab") {
      var f = $$("button", galeria), primeiro = f[0], ultimo = f[f.length - 1];
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
