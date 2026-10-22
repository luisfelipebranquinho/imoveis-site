"""Montagem das páginas HTML do site (home, página de cada imóvel e 404)."""

import json
from html import escape
from urllib.parse import quote

from .textos import brl, inteiro_ou_decimal

POR_PAGINA = 24

ROTULO_TIPO = {
    "apartamento": "Apartamento", "casa": "Casa", "casa-em-condominio": "Casa em condomínio",
    "sobrado": "Sobrado", "cobertura": "Cobertura", "studio": "Studio", "loft": "Loft",
    "kitnet": "Kitnet", "terreno": "Terreno", "sitio": "Sítio", "fazenda": "Fazenda",
    "sala": "Sala comercial", "loja": "Loja", "galpao": "Galpão",
}

ICONES = {
    "area": '<path d="M4 9V4h5M15 4h5v5M20 15v5h-5M9 20H4v-5"/>',
    "quartos": '<path d="M3 18v-6.5A1.5 1.5 0 0 1 4.5 10h15a1.5 1.5 0 0 1 1.5 1.5V18M3 15h18M6 10V7.5A1.5 1.5 0 0 1 7.5 6h9A1.5 1.5 0 0 1 18 7.5V10"/>',
    "banheiros": '<path d="M4 12h16v2a5 5 0 0 1-5 5H9a5 5 0 0 1-5-5v-2zM7 12V6.5A2.5 2.5 0 0 1 9.5 4c1.1 0 2 .6 2.4 1.5M8 19l-1 2M16 19l1 2"/>',
    "vagas": '<path d="M5 16V11l2-4.5A2 2 0 0 1 8.8 5.3h6.4A2 2 0 0 1 17 6.5L19 11v5M5 16h14M5 16v2M19 16v2M7.5 13.2h.01M16.5 13.2h.01M5 11h14"/>',
    "whatsapp": '<path d="M5.5 18.5 4 21l2.6-1.4A9 9 0 1 0 3 12c0 1.6.4 3.1 1.2 4.4"/><path d="M9 8.5c0 3.3 2.2 6 5.5 6.5l1.3-1.5-1.8-1-1 .8c-1.1-.4-2.1-1.4-2.5-2.5l.8-1-1-1.8L9 8.5z"/>',
    "email": '<path d="M4 6h16v12H4z"/><path d="m4 7 8 6 8-6"/>',
    "voltar": '<path d="M15 5l-7 7 7 7"/>',
    "fotos": '<path d="M4 6h16v12H4z"/><path d="m4 15 4.5-4.5 4 4 2.5-2.5L20 17M15 9.5h.01"/>',
}


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


def link_whatsapp(cfg, p=None):
    numero = "".join(ch for ch in cfg.get("whatsapp", "") if ch.isdigit())
    if p:
        modelo = cfg.get("mensagem_whatsapp") or "Olá! Tenho interesse no imóvel {codigo}. {link}"
        link = cfg["site_url"].rstrip("/") + f"/imovel/{p['codigo']}/"
        texto = modelo.format(codigo=p["codigo"], titulo=p["titulo"], link=link)
    else:
        texto = cfg.get("mensagem_whatsapp_geral") or "Olá! Vi seu site de imóveis e gostaria de ajuda."
    return f"https://wa.me/{numero}?text={quote(texto)}"


def link_email(cfg, p=None):
    if p:
        assunto = f"Interesse no imóvel {p['codigo']}"
        link = cfg["site_url"].rstrip("/") + f"/imovel/{p['codigo']}/"
        corpo = f"Olá! Gostaria de mais informações sobre o imóvel {p['codigo']} ({p['titulo']}).\n\n{link}"
    else:
        assunto, corpo = "Contato pelo site", "Olá! Gostaria de ajuda para encontrar um imóvel."
    return f"mailto:{cfg['email']}?subject={quote(assunto)}&body={quote(corpo)}"


def _fatos(p, compacto=True):
    itens = []
    if p.get("area"):
        itens.append(("area", area_txt(p["area"]), "Área"))
    if p.get("quartos") is not None:
        q = p["quartos"]
        extra = f" ({p['suites']} suíte{'s' if p['suites'] != 1 else ''})" if p.get("suites") and not compacto else ""
        itens.append(("quartos", f"{q} quarto{'s' if q != 1 else ''}{extra}", "Quartos"))
    if p.get("banheiros") is not None:
        b = p["banheiros"]
        itens.append(("banheiros", f"{b} banheiro{'s' if b != 1 else ''}", "Banheiros"))
    if p.get("vagas") is not None:
        v = p["vagas"]
        itens.append(("vagas", f"{v} vaga{'s' if v != 1 else ''}", "Vagas"))
    return itens


def card(p, base, destaque_principal=False):
    foto = p["fotos"][0] if p["fotos"] else ""
    fatos = "".join(f'<li>{icone(i)}<span>{e(t)}</span></li>' for i, t, _ in _fatos(p))
    selos = []
    if p.get("destaque"):
        selos.append('<span class="selo">Destaque</span>')
    if p.get("lancamento"):
        selos.append('<span class="selo selo-claro">Lançamento</span>')
    dados = {
        "tipo": p["tipo"], "bairro": p["bairro"], "preco": p.get("preco") or 0,
        "quartos": p.get("quartos") or 0, "area": p.get("area") or 0,
        "ordem": p.get("_ordem", 0), "destaque": 1 if p.get("destaque") else 0,
    }
    attrs = " ".join(f'data-{k}="{e(v)}"' for k, v in dados.items())
    img = (f'<img src="{e(foto)}" alt="" loading="lazy" decoding="async" referrerpolicy="no-referrer">'
           if foto else '<span class="sem-foto">Fotos em breve</span>')
    return f"""
<article class="card{' card-largo' if destaque_principal else ''}" {attrs}>
  <a class="card-link" href="{base}imovel/{e(p['codigo'])}/">
    <div class="card-foto">{img}<div class="selos">{''.join(selos)}</div></div>
    <div class="card-corpo">
      <p class="card-local">{e(p['bairro'])}, {e(p['cidade'])}</p>
      <h3 class="card-titulo">{e(tipo_rotulo(p['tipo']))} {('com ' + area_txt(p['area'])) if p.get('area') else ''}</h3>
      <p class="card-preco">{e(brl(p.get('preco')))}</p>
      <ul class="fatos">{fatos}</ul>
    </div>
  </a>
</article>"""


def dados_vitrine(imoveis):
    """Versão compacta dos imóveis para filtrar e paginar no navegador."""
    return [{
        "c": p["codigo"], "t": p["tipo"], "tr": tipo_rotulo(p["tipo"]), "b": p["bairro"], "ci": p["cidade"],
        "p": p.get("preco") or 0, "a": p.get("area") or 0, "q": p.get("quartos"), "bh": p.get("banheiros"),
        "v": p.get("vagas"), "f": p["fotos"][0] if p["fotos"] else "",
        "d": 1 if p.get("destaque") else 0, "l": 1 if p.get("lancamento") else 0,
    } for p in imoveis]


def _cabeca(cfg, titulo, descricao, base, canonico, imagem=None):
    fonte = ("https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,300..800"
             "&display=swap")
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
<meta name="theme-color" content="#0f2e33">
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
    <a class="marca" href="{base}">{e(cfg['nome'])}</a>
    <nav class="topo-nav" aria-label="Principal">
      <a href="{base}#imoveis">Imóveis</a>
      <a href="{base}#contato">Contato</a>
      <a class="botao botao-pequeno" href="{e(link_whatsapp(cfg))}" target="_blank" rel="noopener">{icone('whatsapp')}<span>WhatsApp</span></a>
    </nav>
  </div>
</header>"""


def _rodape(cfg, base, atualizado):
    creci = f"<p>CRECI {e(cfg['creci'])}</p>" if cfg.get("creci") else ""
    parceria = f"<p>{e(cfg['texto_parceria'])}</p>" if cfg.get("texto_parceria") else ""
    return f"""
<footer class="rodape" id="contato">
  <div class="rodape-in">
    <div class="rodape-chamada">
      <h2>Quer visitar um imóvel ou tirar uma dúvida?</h2>
      <p>Fale direto com {e(cfg.get('responsavel') or cfg['nome'])}: conte qual imóvel chamou sua atenção e combine uma visita.</p>
      <div class="acoes">
        <a class="botao botao-claro" href="{e(link_whatsapp(cfg))}" target="_blank" rel="noopener">{icone('whatsapp')}<span>Conversar no WhatsApp</span></a>
        <a class="botao botao-contorno-claro" href="{e(link_email(cfg))}">{icone('email')}<span>Enviar e-mail</span></a>
      </div>
    </div>
    <div class="rodape-info">
      <p class="marca marca-clara">{e(cfg['nome'])}</p>
      {creci}
      <p>{e(cfg.get('telefone', ''))}</p>
      <p><a href="mailto:{e(cfg['email'])}">{e(cfg['email'])}</a></p>
      {parceria}
      <p class="rodape-nota">Valores e disponibilidade sujeitos a confirmação. Atualizado em {e(atualizado)}.</p>
    </div>
  </div>
</footer>"""


def pagina_inicial(cfg, imoveis, atualizado):
    base = "./"
    com_foto = [p for p in imoveis if p["fotos"]]
    destaques = [p for p in com_foto if p.get("destaque")]
    capa = destaques[0] if destaques else (max(com_foto, key=lambda p: p.get("preco") or 0) if com_foto else None)
    bairros = sorted({p["bairro"] for p in imoveis if p["bairro"]})
    tipos = sorted({p["tipo"] for p in imoveis}, key=tipo_rotulo)

    if capa:
        hero_foto = f"""
      <a class="arco" href="{base}imovel/{e(capa['codigo'])}/">
        <img src="{e(capa['fotos'][0])}" alt="{e(tipo_rotulo(capa['tipo']))} em {e(capa['bairro'])}" fetchpriority="high" referrerpolicy="no-referrer">
        <span class="arco-legenda"><strong>{e(capa['bairro'])}</strong><span>{e(brl(capa.get('preco')))}</span></span>
      </a>"""
    else:
        hero_foto = '<div class="arco arco-vazio"></div>'

    opcoes_tipo = "".join(f'<option value="{e(t)}">{e(tipo_rotulo(t))}</option>' for t in tipos)
    opcoes_bairro = "".join(f'<option value="{e(b)}">{e(b)}</option>' for b in bairros)
    # Só a primeira página vai no HTML; o restante é carregado sob demanda (dados/vitrine.json).
    cartoes = "".join(card(p, base) for p in imoveis[:POR_PAGINA])
    icones_js = "".join(f'<span data-icone="{n}">{icone(n)}</span>' for n in ("area", "quartos", "banheiros", "vagas"))
    total = len(imoveis)
    descricao = (f"{total} imóveis à venda em {cfg.get('cidade_principal', 'Florianópolis')} e região, "
                 f"com fotos e atendimento direto com {cfg.get('responsavel') or cfg['nome']}.")
    vazio = "" if imoveis else '<p class="vazio">Nenhum imóvel publicado no momento. Fale com a gente pelo WhatsApp.</p>'

    return f"""{_cabeca(cfg, f"{cfg['nome']} | Imóveis à venda", descricao, base, cfg['site_url'].rstrip('/') + '/', capa['fotos'][0] if capa else None)}
<body class="pg-inicio">
<a class="pular" href="#imoveis">Pular para os imóveis</a>
{_topo(cfg, base)}
<main>
  <section class="hero">
    <div class="hero-texto">
      <h1>{e(cfg.get('frase_principal') or 'Imóveis em Florianópolis, escolhidos com calma.')}</h1>
      <p class="hero-sub">{e(cfg.get('frase_apoio') or 'Casas e apartamentos à venda na Ilha e no continente, com atendimento de quem conhece cada bairro.')}</p>
      <div class="acoes">
        <a class="botao" href="#imoveis">Ver os {total} imóveis</a>
        <a class="botao botao-contorno" href="{e(link_whatsapp(cfg))}" target="_blank" rel="noopener">{icone('whatsapp')}<span>Conversar no WhatsApp</span></a>
      </div>
    </div>
    <div class="hero-foto">{hero_foto}</div>
  </section>

  <section class="vitrine" id="imoveis" aria-labelledby="titulo-vitrine">
    <div class="vitrine-topo">
      <h2 id="titulo-vitrine">Imóveis à venda</h2>
      <form class="filtros" id="filtros" role="search" aria-label="Filtrar imóveis">
        <label><span>Tipo</span><select name="tipo"><option value="">Todos</option>{opcoes_tipo}</select></label>
        <label><span>Bairro</span><select name="bairro"><option value="">Todos</option>{opcoes_bairro}</select></label>
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
      <p class="contagem" id="contagem" aria-live="polite">{total} imóve{'is' if total != 1 else 'l'}</p>
    </div>
    <div class="grade" id="grade" data-dados="{base}dados/vitrine.json" data-por-pagina="{POR_PAGINA}">{cartoes}</div>
    <template id="icones">{icones_js}</template>
    <p class="vazio" id="sem-resultado" hidden>Nenhum imóvel com esses filtros. <button type="button" class="link" id="limpar">Limpar filtros</button></p>
    <div class="mais"><button type="button" class="botao botao-contorno" id="mostrar-mais"{' hidden' if total <= POR_PAGINA else ''}>Mostrar mais imóveis</button></div>
    {vazio}
  </section>
</main>
{_rodape(cfg, base, atualizado)}
</body>
</html>
"""


def pagina_imovel(cfg, p, semelhantes, atualizado):
    base = "../../"
    url = cfg["site_url"].rstrip("/") + f"/imovel/{p['codigo']}/"
    titulo_pg = f"{tipo_rotulo(p['tipo'])} em {p['bairro']}, {p['cidade']} | {cfg['nome']}"
    resumo = (p.get("descricao") or p["titulo"]).replace("\n", " ")[:155]
    fotos = p["fotos"]

    if fotos:
        miniaturas = "".join(
            f'<button type="button" class="mosaico-mini" data-foto="{i}" aria-label="Abrir foto {i + 1}">'
            f'<img src="{e(u)}" alt="" loading="lazy" referrerpolicy="no-referrer"></button>'
            for i, u in enumerate(fotos[1:5], start=1))
        mosaico = f"""
    <div class="mosaico{' mosaico-unico' if len(fotos) == 1 else ''}">
      <button type="button" class="mosaico-principal" data-foto="0" aria-label="Abrir galeria de fotos">
        <img src="{e(fotos[0])}" alt="{e(p['titulo'])}" fetchpriority="high" referrerpolicy="no-referrer">
      </button>
      {miniaturas}
      <button type="button" class="ver-fotos" data-foto="0">{icone('fotos')}<span>Ver as {len(fotos)} fotos</span></button>
    </div>"""
    else:
        mosaico = '<div class="mosaico mosaico-vazio"><p>Fotos em breve</p></div>'

    fatos = "".join(f'<li>{icone(i, "icone icone-grande")}<strong>{e(t)}</strong></li>'
                    for i, t, _ in _fatos(p, compacto=False))
    preco_m2 = ""
    if p.get("preco") and p.get("area"):
        preco_m2 = f'<p class="preco-detalhe">{e(brl(p["preco"] / p["area"]))} por m²</p>'
    taxas = ""
    if p.get("condominio"):
        taxas += f'<div><dt>Condomínio</dt><dd>{e(brl(p["condominio"]))}/mês</dd></div>'
    if p.get("iptu"):
        per = {"Monthly": "/mês", "Yearly": "/ano"}.get(p.get("periodo_iptu"), "")
        taxas += f'<div><dt>IPTU</dt><dd>{e(brl(p["iptu"]))}{per}</dd></div>'
    taxas = f'<dl class="taxas">{taxas}</dl>' if taxas else ""

    descricao = ""
    if p.get("descricao"):
        paragrafos = "".join(f"<p>{e(par)}</p>" for par in p["descricao"].split("\n\n") if par.strip())
        paragrafos = paragrafos.replace("\n", "<br>")
        descricao = f"""
      <section class="bloco">
        <h2>Sobre o imóvel</h2>
        <div class="descricao" id="descricao">{paragrafos}</div>
        <button type="button" class="link ler-mais" id="ler-mais" hidden aria-expanded="false" aria-controls="descricao">Ler descrição completa</button>
      </section>"""

    def lista(titulo, itens):
        if not itens:
            return ""
        lis = "".join(f"<li>{e(i)}</li>" for i in itens)
        return f'<section class="bloco"><h2>{titulo}</h2><ul class="etiquetas">{lis}</ul></section>'

    video = ""
    if p.get("video"):
        video = (f'<section class="bloco"><h2>Vídeo</h2><div class="video"><iframe src="{e(p["video"])}" '
                 f'title="Vídeo do imóvel" loading="lazy" allowfullscreen></iframe></div></section>')

    local = f"{p['bairro']}, {p['cidade']} - {p['uf']}"
    rua = f'<p class="rua">{e(p["endereco"])}</p>' if p.get("endereco") else ""
    outros = ""
    if semelhantes:
        outros = f"""
  <section class="semelhantes" aria-labelledby="titulo-semelhantes">
    <h2 id="titulo-semelhantes">Você também pode gostar</h2>
    <div class="grade grade-tres">{''.join(card(s, base) for s in semelhantes)}</div>
  </section>"""

    whats = e(link_whatsapp(cfg, p))
    email = e(link_email(cfg, p))
    dados_fotos = escape(json.dumps(fotos), quote=True)

    return f"""{_cabeca(cfg, titulo_pg, resumo, base, url, fotos[0] if fotos else None)}
<body class="pg-imovel">
{_topo(cfg, base)}
<main class="imovel">
  <a class="voltar" href="{base}#imoveis">{icone('voltar')}<span>Todos os imóveis</span></a>
  {mosaico}
  <div class="imovel-grade">
    <div class="imovel-conteudo">
      <header class="imovel-cabeca">
        <p class="imovel-local">{e(local)}</p>
        <h1>{e(p['titulo'])}</h1>
        {rua}
        <p class="codigo">Código {e(p['codigo'])}</p>
      </header>
      <ul class="fatos-grandes">{fatos}</ul>
      {descricao}
      {lista('No imóvel', p.get('caracteristicas', []))}
      {lista('No condomínio', p.get('caracteristicas_condominio', []))}
      {video}
    </div>
    <aside class="painel" aria-label="Valor e contato">
      <p class="painel-rotulo">Valor de venda</p>
      <p class="preco">{e(brl(p.get('preco')))}</p>
      {preco_m2}
      {taxas}
      <a class="botao botao-cheio" href="{whats}" target="_blank" rel="noopener">{icone('whatsapp')}<span>Conversar no WhatsApp</span></a>
      <a class="botao botao-contorno botao-cheio" href="{email}">{icone('email')}<span>Enviar e-mail</span></a>
      <p class="painel-nota">Atendimento com {e(cfg.get('responsavel') or cfg['nome'])}. Informe o código {e(p['codigo'])}.</p>
    </aside>
  </div>
  {outros}
</main>
<div class="barra-contato" aria-label="Contato rápido">
  <div><span class="barra-preco">{e(brl(p.get('preco')))}</span><span class="barra-cod">Código {e(p['codigo'])}</span></div>
  <a class="botao" href="{whats}" target="_blank" rel="noopener">{icone('whatsapp')}<span>WhatsApp</span></a>
</div>
<div class="galeria" id="galeria" hidden role="dialog" aria-modal="true" aria-label="Fotos do imóvel" data-fotos="{dados_fotos}">
  <button type="button" class="galeria-fechar" aria-label="Fechar galeria">Fechar</button>
  <button type="button" class="galeria-seta galeria-ant" aria-label="Foto anterior">‹</button>
  <figure><img alt="" referrerpolicy="no-referrer"><figcaption></figcaption></figure>
  <button type="button" class="galeria-seta galeria-prox" aria-label="Próxima foto">›</button>
</div>
{_rodape(cfg, base, atualizado)}
</body>
</html>
"""


def pagina_404(cfg):
    base = "/" + cfg["site_url"].rstrip("/").split("/", 3)[3] + "/" if cfg["site_url"].count("/") > 2 else "/"
    return f"""{_cabeca(cfg, f"Página não encontrada | {cfg['nome']}", "Página não encontrada.", base, cfg['site_url'])}
<body>
{_topo(cfg, base)}
<main class="erro">
  <h1>Este imóvel não está mais aqui</h1>
  <p>Ele pode ter sido vendido ou retirado do site. Veja os imóveis disponíveis ou fale com a gente.</p>
  <div class="acoes">
    <a class="botao" href="{base}#imoveis">Ver imóveis disponíveis</a>
    <a class="botao botao-contorno" href="{e(link_whatsapp(cfg))}" target="_blank" rel="noopener">{icone('whatsapp')}<span>Conversar no WhatsApp</span></a>
  </div>
</main>
</body>
</html>
"""
