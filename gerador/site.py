"""Montagem das páginas HTML do site (home, página de cada imóvel e 404)."""

import json
from html import escape
from urllib.parse import quote

from .regioes import ORDEM as ORDEM_REGIOES
from .textos import brl, inteiro_ou_decimal

POR_PAGINA = 24

ROTULO_TIPO = {
    "apartamento": "Apartamento", "casa": "Casa", "casa-em-condominio": "Casa em condomínio",
    "sobrado": "Sobrado", "cobertura": "Cobertura", "studio": "Studio", "loft": "Loft",
    "kitnet": "Kitnet", "terreno": "Terreno", "terreno-condominio": "Terreno em condomínio",
    "sitio": "Sítio", "sitio-fazenda": "Sítio / fazenda", "fazenda": "Fazenda", "sala": "Sala comercial",
    "loja": "Loja", "galpao": "Galpão", "hotel-pousada": "Hotel / pousada", "flat": "Flat",
    "predio-comercial": "Prédio comercial", "predio-residencial": "Prédio residencial",
    "box-garagem": "Box de garagem",
}

ICONES = {
    "area": '<path d="M4 9V4h5M15 4h5v5M20 15v5h-5M9 20H4v-5"/>',
    "quartos": '<path d="M3 18v-6.5A1.5 1.5 0 0 1 4.5 10h15a1.5 1.5 0 0 1 1.5 1.5V18M3 15h18M6 10V7.5A1.5 1.5 0 0 1 7.5 6h9A1.5 1.5 0 0 1 18 7.5V10"/>',
    "banheiros": '<path d="M4 12h16v2a5 5 0 0 1-5 5H9a5 5 0 0 1-5-5v-2zM7 12V6.5A2.5 2.5 0 0 1 9.5 4c1.1 0 2 .6 2.4 1.5M8 19l-1 2M16 19l1 2"/>',
    "vagas": '<path d="M5 16V11l2-4.5A2 2 0 0 1 8.8 5.3h6.4A2 2 0 0 1 17 6.5L19 11v5M5 16h14M5 16v2M19 16v2M7.5 13.2h.01M16.5 13.2h.01M5 11h14"/>',
    "whatsapp": '<path d="M5.5 18.5 4 21l2.6-1.4A9 9 0 1 0 3 12c0 1.6.4 3.1 1.2 4.4"/><path d="M9 8.5c0 3.3 2.2 6 5.5 6.5l1.3-1.5-1.8-1-1 .8c-1.1-.4-2.1-1.4-2.5-2.5l.8-1-1-1.8L9 8.5z"/>',
    "email": '<path d="M4 6h16v12H4z"/><path d="m4 7 8 6 8-6"/>',
    "fotos": '<path d="M4 6h16v12H4z"/><path d="m4 15 4.5-4.5 4 4 2.5-2.5L20 17M15 9.5h.01"/>',
    "video": '<path d="M4 7h11v10H4zM15 10.5 20 8v8l-5-2.5"/>',
    "local": '<path d="M12 21s-6.5-5.6-6.5-11a6.5 6.5 0 0 1 13 0C18.5 15.4 12 21 12 21z"/><circle cx="12" cy="10" r="2.3"/>',
    "busca": '<circle cx="11" cy="11" r="6.5"/><path d="m20 20-4.4-4.4"/>',
    "esq": '<path d="M15 5l-7 7 7 7"/>',
    "dir": '<path d="M9 5l7 7-7 7"/>',
    "telefone": '<path d="M5 4h4l2 5-2.5 1.5a11 11 0 0 0 5 5L15 13l5 2v4a2 2 0 0 1-2 2A16 16 0 0 1 3 6a2 2 0 0 1 2-2"/>',
    "relogio": '<circle cx="12" cy="12" r="8.5"/><path d="M12 7.5V12l3 2"/>',
}

ONDA = ('<svg class="marca-onda" viewBox="0 0 32 32" aria-hidden="true"><circle cx="16" cy="16" r="15" '
        'fill="currentColor"/><path d="M6 19c2.5 0 2.5-2.5 5-2.5s2.5 2.5 5 2.5 2.5-2.5 5-2.5 2.5 2.5 5 2.5" '
        'fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round"/><path d="M9 13.5c2.2-3.5 4.4-5 '
        '7-5s4.8 1.5 7 5" fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round" opacity=".7"/></svg>')


def icone(nome, classe="icone"):
    return (f'<svg class="{classe}" viewBox="0 0 24 24" aria-hidden="true" fill="none" '
            f'stroke="currentColor" stroke-width="1.6" stroke-linecap="round" '
            f'stroke-linejoin="round">{ICONES[nome]}</svg>')


def e(texto) -> str:
    return escape(str(texto or ""), quote=True)


def tipo_rotulo(tipo):
    return ROTULO_TIPO.get(tipo, (tipo or "Imóvel").replace("-", " ").capitalize())


def area_txt(n):
    return f"{str(inteiro_ou_decimal(n)).replace('.', ',')} m²"


def link_pagina(cfg, p):
    return cfg["site_url"].rstrip("/") + f"/imovel/{p['codigo']}/"


def mensagem_imovel(cfg, p):
    modelo = cfg.get("mensagem_whatsapp") or "Olá! Tenho interesse no imóvel código {codigo}. {link}"
    return modelo.format(codigo=p["codigo"], titulo=p["titulo"], link=link_pagina(cfg, p))


def numero_whatsapp(cfg):
    return "".join(ch for ch in cfg.get("whatsapp", "") if ch.isdigit())


def link_whatsapp(cfg, p=None):
    texto = mensagem_imovel(cfg, p) if p else (
        cfg.get("mensagem_whatsapp_geral") or "Olá! Vi o site e gostaria de ajuda para encontrar um imóvel.")
    return f"https://wa.me/{numero_whatsapp(cfg)}?text={quote(texto)}"


def link_email(cfg, p=None):
    if p:
        assunto = f"Interesse no imóvel {p['codigo']}"
        corpo = (f"Olá! Gostaria de mais informações sobre o imóvel {p['codigo']} ({p['titulo']}).\n\n"
                 f"{link_pagina(cfg, p)}")
    else:
        assunto, corpo = "Contato pelo site", "Olá! Gostaria de ajuda para encontrar um imóvel."
    return f"mailto:{cfg['email']}?subject={quote(assunto)}&body={quote(corpo)}"


def _plural(n, um, varios):
    return f"{n} {um if n == 1 else varios}"


# ---------------------------------------------------------------- cartões

def card(p, base):
    foto = p["fotos"][0] if p["fotos"] else ""
    img = (f'<img src="{e(foto)}" alt="" loading="lazy" decoding="async" referrerpolicy="no-referrer">'
           if foto else '<span class="sem-foto">Fotos em breve</span>')
    selos = '<span class="selo">Destaque</span>' if p.get("destaque") else ""
    if p.get("lancamento"):
        selos += '<span class="selo">Lançamento</span>'
    fatos = []
    if p.get("area"):
        fatos.append(("area", area_txt(p["area"]), "Área"))
    if p.get("quartos") is not None:
        fatos.append(("quartos", str(p["quartos"]), "Quartos"))
    if p.get("vagas") is not None:
        fatos.append(("vagas", str(p["vagas"]), "Vagas"))
    lis = "".join(f'<li title="{r}">{icone(i)}<span><span class="sr">{r}: </span>{e(t)}</span></li>'
                  for i, t, r in fatos)
    return f"""<article class="card">
  <a class="card-link" href="{base}imovel/{e(p['codigo'])}/">
    <div class="card-foto">{img}<span class="pilula">{e(p['bairro'])}</span><span class="etiqueta">{e(tipo_rotulo(p['tipo']))}</span>{f'<div class="selos">{selos}</div>' if selos else ''}</div>
    <div class="card-corpo">
      <h3 class="card-titulo">{e(tipo_rotulo(p['tipo']))}</h3>
      <p class="card-local">{e(p['bairro'])}, {e(p['cidade'])} - {e(p['uf'])}</p>
      <p class="card-preco">{e(brl(p.get('preco')))}</p>
      <ul class="fatos">{lis}</ul>
    </div>
  </a>
</article>"""


def dados_vitrine(imoveis):
    """Versão compacta dos imóveis para filtrar e paginar no navegador."""
    return [{
        "c": p["codigo"], "t": p["tipo"], "tr": tipo_rotulo(p["tipo"]), "b": p["bairro"], "ci": p["cidade"],
        "u": p["uf"], "r": p.get("regiao", ""), "p": p.get("preco") or 0, "a": p.get("area") or 0,
        "q": p.get("quartos"), "v": p.get("vagas"), "f": p["fotos"][0] if p["fotos"] else "",
        "d": 1 if p.get("destaque") else 0, "l": 1 if p.get("lancamento") else 0,
    } for p in imoveis]


def carrossel(id_, titulo, itens, base, fundo=False, link_todos=None):
    if not itens:
        return ""
    cartoes = "".join(f'<div class="carrossel-item">{card(p, base)}</div>' for p in itens)
    todos = f'<a class="link-secao" href="{link_todos}">Ver todos</a>' if link_todos else ""
    return f"""
<section class="secao{' secao-cinza' if fundo else ''}" aria-labelledby="t-{id_}">
  <div class="secao-in">
    <div class="secao-topo">
      <h2 id="t-{id_}">{e(titulo)}</h2>
      <div class="secao-acoes">{todos}
        <button type="button" class="seta" data-rolar="{id_}" data-dir="-1" aria-label="Anteriores">{icone('esq')}</button>
        <button type="button" class="seta" data-rolar="{id_}" data-dir="1" aria-label="Próximos">{icone('dir')}</button>
      </div>
    </div>
    <div class="carrossel" id="{id_}" tabindex="0" aria-label="{e(titulo)}">{cartoes}</div>
  </div>
</section>"""


# ---------------------------------------------------------------- partes comuns

def _cabeca(cfg, titulo, descricao, base, canonico, imagem=None):
    fonte = "https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap"
    og_img = f'<meta property="og:image" content="{e(imagem)}">' if imagem else ""
    return f"""<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(titulo)}</title>
<meta name="description" content="{e(descricao)}">
<link rel="canonical" href="{e(canonico)}">
<meta property="og:title" content="{e(titulo)}">
<meta property="og:description" content="{e(descricao)}">
<meta property="og:type" content="website">
<meta property="og:url" content="{e(canonico)}">
{og_img}
<meta name="theme-color" content="#0b2a3f">
<link rel="icon" href="{base}assets/favicon.svg" type="image/svg+xml">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="{fonte}">
<link rel="stylesheet" href="{base}assets/style.css">
<script src="{base}assets/app.js" defer></script>
</head>"""


def _topo(cfg, base):
    return f"""
<header class="topo">
  <div class="topo-in">
    <a class="marca" href="{base}">{ONDA}<span>{e(cfg['nome'])}</span></a>
    <nav class="topo-nav" aria-label="Principal">
      <a href="{base}#imoveis">Imóveis</a>
      <a href="{base}#regioes">Regiões</a>
      <a href="{base}#contato">Contato</a>
    </nav>
    <a class="botao botao-pequeno" href="{e(link_whatsapp(cfg))}" target="_blank" rel="noopener">{icone('whatsapp')}<span>WhatsApp</span></a>
  </div>
</header>"""


def _faixa_contato(cfg):
    return f"""
<section class="faixa" aria-labelledby="t-faixa">
  <div class="faixa-in">
    <div>
      <h2 id="t-faixa">Ainda não encontrou seu imóvel?</h2>
      <p>Conte para a {e(cfg['nome'])} o que você procura: bairro, tamanho e faixa de valor. A gente seleciona as opções para você.</p>
    </div>
    <a class="botao botao-claro" href="{e(link_whatsapp(cfg))}" target="_blank" rel="noopener">{icone('whatsapp')}<span>Falar no WhatsApp</span></a>
  </div>
</section>"""


def _rodape(cfg, base, atualizado):
    linhas = []
    if cfg.get("telefone"):
        linhas.append(f'<li>{icone("telefone")}<span>{e(cfg["telefone"])}</span></li>')
    linhas.append(f'<li>{icone("email")}<a href="mailto:{e(cfg["email"])}">{e(cfg["email"])}</a></li>')
    linhas.append(f'<li>{icone("whatsapp")}<a href="{e(link_whatsapp(cfg))}" target="_blank" rel="noopener">WhatsApp</a></li>')
    if cfg.get("horario"):
        linhas.append(f'<li>{icone("relogio")}<span>{e(cfg["horario"])}</span></li>')
    redes = []
    for nome in ("instagram", "facebook", "linkedin", "youtube"):
        if cfg.get(nome):
            redes.append(f'<a href="{e(cfg[nome])}" target="_blank" rel="noopener">{nome.capitalize()}</a>')
    redes_html = f'<p class="redes">{" ".join(redes)}</p>' if redes else ""
    creci = f" · CRECI {e(cfg['creci'])}" if cfg.get("creci") else ""
    parceria = f"<p>{e(cfg['texto_parceria'])}</p>" if cfg.get("texto_parceria") else ""
    return f"""
<footer class="rodape" id="contato">
  <div class="rodape-in">
    <div>
      <a class="marca marca-clara" href="{base}">{ONDA}<span>{e(cfg['nome'])}</span></a>
      <p class="rodape-texto">Imóveis à venda na Grande Florianópolis, com atendimento direto pelo WhatsApp.</p>
      {redes_html}
    </div>
    <div>
      <h2>Contato</h2>
      <ul class="rodape-lista">{''.join(linhas)}</ul>
    </div>
  </div>
  <div class="rodape-base">
    <p>© {e(cfg['nome'])}{creci}</p>
    {parceria}
    <p>Valores e disponibilidade sujeitos a confirmação. Atualizado em {e(atualizado)}.</p>
  </div>
</footer>"""


# ---------------------------------------------------------------- página inicial

def _regioes_html(imoveis, base):
    grupos = {}
    for p in imoveis:
        grupos.setdefault(p.get("regiao") or "Outras", []).append(p)
    ordem = [r for r in ORDEM_REGIOES if r in grupos]
    ordem += sorted((r for r in grupos if r not in ordem), key=lambda r: -len(grupos[r]))
    ordem = [r for r in ordem if len(grupos[r]) >= 3][:8]
    if len(ordem) < 2:
        return ""
    tiles = []
    for i, r in enumerate(ordem):
        com_foto = [p for p in grupos[r] if p["fotos"]]
        capa = max(com_foto, key=lambda p: p.get("preco") or 0) if com_foto else None
        img = (f'<img src="{e(capa["fotos"][0])}" alt="" loading="lazy" referrerpolicy="no-referrer">'
               if capa else "")
        tiles.append(f'<a class="regiao{" regiao-alta" if i == 0 else ""}" href="{base}?regiao={quote(r)}#imoveis">'
                     f'{img}<span class="regiao-nome">{e(r)}</span>'
                     f'<span class="regiao-qtd">{_plural(len(grupos[r]), "imóvel", "imóveis")}</span></a>')
    return f"""
<section class="secao" id="regioes" aria-labelledby="t-regioes">
  <div class="secao-in">
    <h2 id="t-regioes" class="titulo-centro">Imóveis na Grande Florianópolis</h2>
    <div class="regioes">{''.join(tiles)}</div>
  </div>
</section>"""


def pagina_inicial(cfg, imoveis, atualizado):
    base = "./"
    com_foto = [p for p in imoveis if p["fotos"]]
    destaques = [p for p in com_foto if p.get("destaque")]
    capa_url = cfg.get("imagem_capa") or ""
    if not capa_url and com_foto:
        capa_url = (destaques[0] if destaques else max(com_foto, key=lambda p: p.get("preco") or 0))["fotos"][0]

    tipos = sorted({p["tipo"] for p in imoveis}, key=tipo_rotulo)
    bairros = sorted({p["bairro"] for p in imoveis if p["bairro"]})
    regioes = sorted({p.get("regiao") for p in imoveis if p.get("regiao")},
                     key=lambda r: (ORDEM_REGIOES.index(r) if r in ORDEM_REGIOES else 99, r))
    opt = lambda vals, rot=lambda v: v: "".join(f'<option value="{e(v)}">{e(rot(v))}</option>' for v in vals)
    total = len(imoveis)

    if destaques:
        bloco1 = carrossel("destaques", "Imóveis em destaque", destaques[:12], base)
    else:
        recentes = sorted(com_foto, key=lambda p: p.get("primeira_vez", ""), reverse=True)[:12]
        bloco1 = carrossel("novidades", "Novidades no site", recentes, base)
    alto = sorted((p for p in com_foto if (p.get("preco") or 0) >= cfg.get("alto_padrao_a_partir", 2500000)),
                  key=lambda p: p.get("preco") or 0, reverse=True)[:12]
    bloco2 = carrossel("alto-padrao", "Alto padrão", alto, base, fundo=True,
                       link_todos=f"{base}?ordem=maior#imoveis")

    cartoes = "".join(card(p, base) for p in imoveis[:POR_PAGINA])
    icones_js = "".join(f'<span data-icone="{n}">{icone(n)}</span>' for n in ("area", "quartos", "vagas"))
    descricao = (f"{total} imóveis à venda na Grande Florianópolis: apartamentos, casas e terrenos. "
                 f"Atendimento direto com a {cfg['nome']} pelo WhatsApp.")
    estilo_capa = f' style="--capa: url(\'{e(capa_url)}\')"' if capa_url else ""

    return f"""{_cabeca(cfg, f"{cfg['nome']} | Imóveis à venda na Grande Florianópolis", descricao, base, cfg['site_url'].rstrip('/') + '/', capa_url or None)}
<body class="pg-inicio">
<a class="pular" href="#imoveis">Pular para os imóveis</a>
{_topo(cfg, base)}
<main>
  <section class="hero"{estilo_capa}>
    <div class="hero-in">
      <h1>{e(cfg.get('frase_principal') or 'Encontre o seu imóvel na Grande Florianópolis')}</h1>
      <p class="hero-sub">{e(cfg.get('frase_apoio') or f'{total} imóveis à venda, de studios a casas de alto padrão.')}</p>
      <form class="busca" id="busca" action="{base}" role="search" aria-label="Buscar imóveis">
        <label class="busca-texto"><span class="sr">Bairro, cidade ou código</span>{icone('busca')}
          <input type="search" name="q" placeholder="Bairro, cidade ou código do imóvel" autocomplete="off" list="lista-bairros"></label>
        <datalist id="lista-bairros">{opt(bairros)}</datalist>
        <label><span class="sr">Tipo de imóvel</span><select name="tipo"><option value="">Tipo de imóvel</option>{opt(tipos, tipo_rotulo)}</select></label>
        <label><span class="sr">Quartos</span><select name="quartos"><option value="">Quartos</option>
          <option value="1">1 ou mais</option><option value="2">2 ou mais</option><option value="3">3 ou mais</option><option value="4">4 ou mais</option></select></label>
        <button class="botao botao-busca" type="submit">{icone('busca')}<span>Buscar</span></button>
      </form>
    </div>
  </section>

  {_regioes_html(imoveis, base)}
  {bloco1}
  {bloco2}

  <section class="secao" id="imoveis" aria-labelledby="t-vitrine">
    <div class="secao-in">
      <div class="secao-topo">
        <h2 id="t-vitrine">Todos os imóveis</h2>
        <p class="contagem" id="contagem" aria-live="polite">{_plural(total, 'imóvel', 'imóveis')}</p>
      </div>
      <form class="filtros" id="filtros" aria-label="Filtrar imóveis">
        <input type="hidden" name="q">
        <label><span>Região</span><select name="regiao"><option value="">Todas</option>{opt(regioes)}</select></label>
        <label><span>Tipo</span><select name="tipo"><option value="">Todos</option>{opt(tipos, tipo_rotulo)}</select></label>
        <label><span>Valor até</span><select name="preco">
          <option value="">Qualquer valor</option><option value="500000">R$ 500 mil</option>
          <option value="800000">R$ 800 mil</option><option value="1000000">R$ 1 milhão</option>
          <option value="1500000">R$ 1,5 milhão</option><option value="2500000">R$ 2,5 milhões</option>
          <option value="5000000">R$ 5 milhões</option></select></label>
        <label><span>Quartos</span><select name="quartos">
          <option value="">Qualquer</option><option value="1">1 ou mais</option><option value="2">2 ou mais</option>
          <option value="3">3 ou mais</option><option value="4">4 ou mais</option></select></label>
        <label><span>Ordenar</span><select name="ordem">
          <option value="">Destaques primeiro</option><option value="menor">Menor valor</option>
          <option value="maior">Maior valor</option><option value="area">Maior área</option></select></label>
      </form>
      <p class="busca-ativa" id="busca-ativa" hidden></p>
      <div class="grade" id="grade" data-dados="{base}dados/vitrine.json" data-por-pagina="{POR_PAGINA}">{cartoes}</div>
      <template id="icones">{icones_js}</template>
      <p class="vazio" id="sem-resultado" hidden>Nenhum imóvel com esses filtros. <button type="button" class="link" id="limpar">Limpar filtros</button></p>
      <div class="mais"><button type="button" class="botao botao-contorno" id="mostrar-mais"{' hidden' if total <= POR_PAGINA else ''}>Mostrar mais imóveis</button></div>
      {'' if imoveis else '<p class="vazio">Nenhum imóvel publicado no momento. Fale com a gente pelo WhatsApp.</p>'}
    </div>
  </section>
  {_faixa_contato(cfg)}
</main>
{_rodape(cfg, base, atualizado)}
</body>
</html>
"""


# ---------------------------------------------------------------- página do imóvel

def pagina_imovel(cfg, p, semelhantes, atualizado):
    base = "../../"
    url = link_pagina(cfg, p)
    titulo_pg = f"{tipo_rotulo(p['tipo'])} em {p['bairro']}, {p['cidade']} | {cfg['nome']}"
    resumo = (p.get("descricao") or p["titulo"]).replace("\n", " ")[:155]
    fotos = p["fotos"]

    if fotos:
        miniaturas = "".join(
            f'<button type="button" class="mini" data-foto="{i}" aria-label="Abrir foto {i + 1}">'
            f'<img src="{e(u)}" alt="" loading="lazy" referrerpolicy="no-referrer"></button>'
            for i, u in enumerate(fotos[1:5], start=1))
        chips = f'<button type="button" class="chip" data-foto="0">{icone("fotos")}<span>{len(fotos)} fotos</span></button>'
        if p.get("video"):
            chips += f'<a class="chip" href="#video">{icone("video")}<span>Vídeo</span></a>'
        galeria = f"""
  <div class="galeria-topo{' galeria-unica' if len(fotos) == 1 else ''}">
    <div class="principal">
      <button type="button" class="principal-foto" data-foto="0" aria-label="Abrir galeria de fotos">
        <img id="foto-principal" src="{e(fotos[0])}" alt="{e(p['titulo'])}" fetchpriority="high" referrerpolicy="no-referrer">
      </button>
      {f'<button type="button" class="seta seta-foto seta-esq" data-passo="-1" aria-label="Foto anterior">{icone("esq")}</button><button type="button" class="seta seta-foto seta-dir" data-passo="1" aria-label="Próxima foto">{icone("dir")}</button>' if len(fotos) > 1 else ''}
      <div class="chips">{chips}</div>
    </div>
    {f'<div class="minis">{miniaturas}</div>' if miniaturas else ''}
  </div>"""
    else:
        galeria = '<div class="galeria-topo galeria-vazia"><p>Fotos em breve</p></div>'

    fatos = []
    if p.get("area"):
        fatos.append(("area", area_txt(p["area"])))
    if p.get("quartos") is not None:
        s = f" ({_plural(p['suites'], 'suíte', 'suítes')})" if p.get("suites") else ""
        fatos.append(("quartos", _plural(p["quartos"], "quarto", "quartos") + s))
    if p.get("banheiros") is not None:
        fatos.append(("banheiros", _plural(p["banheiros"], "banheiro", "banheiros")))
    if p.get("vagas") is not None:
        fatos.append(("vagas", _plural(p["vagas"], "vaga", "vagas")))
    fatos_html = "".join(f"<li>{icone(i)}<span>{e(t)}</span></li>" for i, t in fatos)

    taxas = []
    if p.get("condominio"):
        taxas.append(f"Condomínio {brl(p['condominio'])}/mês")
    if p.get("iptu"):
        per = {"Monthly": "/mês", "Yearly": "/ano"}.get(p.get("periodo_iptu"), "")
        taxas.append(f"IPTU {brl(p['iptu'])}{per}")
    if p.get("preco") and p.get("area"):
        taxas.append(f"{brl(p['preco'] / p['area'])} por m²")
    taxas_html = f'<p class="taxas">{e(" · ".join(taxas))}</p>' if taxas else ""

    descricao = ""
    if p.get("descricao"):
        paragrafos = "".join(f"<p>{e(par)}</p>" for par in p["descricao"].split("\n\n") if par.strip())
        descricao = f"""
      <section class="bloco">
        <h2>Sobre este imóvel</h2>
        <div class="descricao" id="descricao">{paragrafos.replace(chr(10), '<br>')}</div>
        <button type="button" class="link ler-mais" id="ler-mais" hidden aria-expanded="false" aria-controls="descricao">Ler descrição completa</button>
      </section>"""

    def lista(titulo, itens):
        if not itens:
            return ""
        lis = "".join(f"<li>{e(i)}</li>" for i in itens)
        return f'<section class="bloco"><h2>{titulo}</h2><ul class="lista-check">{lis}</ul></section>'

    video = ""
    if p.get("video"):
        video = (f'<section class="bloco" id="video"><h2>Vídeo</h2><div class="video"><iframe src="{e(p["video"])}" '
                 f'title="Vídeo do imóvel" loading="lazy" allowfullscreen></iframe></div></section>')

    selos = '<span class="selo">Destaque</span>' if p.get("destaque") else ""
    if p.get("lancamento"):
        selos += '<span class="selo">Lançamento</span>'
    rua = f"{p['endereco']}, " if p.get("endereco") else ""
    outros = carrossel("semelhantes", "Você também pode gostar", semelhantes, base, fundo=True) if semelhantes else ""
    whats = e(link_whatsapp(cfg, p))
    email = e(link_email(cfg, p))

    return f"""{_cabeca(cfg, titulo_pg, resumo, base, url, fotos[0] if fotos else None)}
<body class="pg-imovel">
{_topo(cfg, base)}
<nav class="trilha" aria-label="Você está em">
  <div class="trilha-in">
    <ol>
      <li><a href="{base}">Início</a></li>
      <li><a href="{base}#imoveis">Imóveis</a></li>
      <li><a href="{base}?tipo={quote(p['tipo'])}#imoveis">{e(tipo_rotulo(p['tipo']))}</a></li>
      <li aria-current="page">{e(p['bairro'])} · Código {e(p['codigo'])}</li>
    </ol>
    <p class="trilha-local"><strong>{e(p['bairro'])}</strong> - {e(p['cidade'])}</p>
  </div>
</nav>
<main class="imovel">
  {galeria}
  <div class="imovel-grade">
    <div class="imovel-conteudo">
      <div class="etiquetas-topo">{selos}<span class="codigo">Cód. {e(p['codigo'])}</span></div>
      <h1>{e(p['titulo'])}</h1>
      <p class="valor">Valor de venda: <strong>{e(brl(p.get('preco')))}</strong></p>
      {taxas_html}
      <p class="endereco">{icone('local')}<span>{e(rua)}{e(p['bairro'])}, {e(p['cidade'])} - {e(p['uf'])}</span></p>
      <ul class="fatos-linha">{fatos_html}</ul>
      {descricao}
      {lista('Infraestrutura do imóvel', p.get('caracteristicas', []))}
      {lista('Infraestrutura do condomínio', p.get('caracteristicas_condominio', []))}
      {video}
    </div>
    <aside class="contato-card" aria-labelledby="t-contato">
      <h2 id="t-contato">Gostou deste imóvel?</h2>
      <p>Fale com a {e(cfg['nome'])} e agende uma visita.</p>
      <form class="form-whats" id="form-whats" data-numero="{e(numero_whatsapp(cfg))}" action="https://wa.me/{e(numero_whatsapp(cfg))}" target="_blank">
        <label><span>Seu nome</span><input name="nome" autocomplete="name" placeholder="Como podemos te chamar?"></label>
        <label><span>Mensagem</span><textarea name="text" rows="4">{e(mensagem_imovel(cfg, p))}</textarea></label>
        <button class="botao botao-cheio" type="submit">{icone('whatsapp')}<span>Enviar pelo WhatsApp</span></button>
      </form>
      <a class="botao botao-contorno botao-cheio" href="{email}">{icone('email')}<span>Enviar e-mail</span></a>
      <p class="contato-nota">Ao enviar, o WhatsApp abre com a mensagem pronta. Nada fica salvo neste site.</p>
    </aside>
  </div>
</main>
{outros}
<div class="barra-contato" aria-label="Contato rápido">
  <div><span class="barra-preco">{e(brl(p.get('preco')))}</span><span class="barra-cod">Cód. {e(p['codigo'])}</span></div>
  <a class="botao" href="{whats}" target="_blank" rel="noopener">{icone('whatsapp')}<span>WhatsApp</span></a>
</div>
<div class="galeria" id="galeria" hidden role="dialog" aria-modal="true" aria-label="Fotos do imóvel" data-fotos="{escape(json.dumps(fotos), quote=True)}">
  <button type="button" class="galeria-fechar" aria-label="Fechar galeria">Fechar</button>
  <button type="button" class="galeria-seta galeria-ant" aria-label="Foto anterior">{icone('esq')}</button>
  <figure><img alt="" referrerpolicy="no-referrer"><figcaption></figcaption></figure>
  <button type="button" class="galeria-seta galeria-prox" aria-label="Próxima foto">{icone('dir')}</button>
</div>
{_faixa_contato(cfg)}
{_rodape(cfg, base, atualizado)}
</body>
</html>
"""


def pagina_404(cfg):
    partes = cfg["site_url"].rstrip("/").split("/", 3)
    base = "/" + partes[3] + "/" if len(partes) > 3 else "/"
    return f"""{_cabeca(cfg, f"Página não encontrada | {cfg['nome']}", "Página não encontrada.", base, cfg['site_url'])}
<body>
{_topo(cfg, base)}
<main class="erro">
  <h1>Este imóvel não está mais aqui</h1>
  <p>Ele pode ter sido vendido ou retirado do site. Veja os imóveis disponíveis ou fale com a gente.</p>
  <div class="acoes">
    <a class="botao" href="{base}#imoveis">Ver imóveis disponíveis</a>
    <a class="botao botao-contorno" href="{e(link_whatsapp(cfg))}" target="_blank" rel="noopener">{icone('whatsapp')}<span>Falar no WhatsApp</span></a>
  </div>
</main>
</body>
</html>
"""
