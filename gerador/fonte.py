"""Acesso ao site da Gralha Imóveis: validação de endereço, download seguro e
descoberta dos anúncios de venda (sitemap + páginas de listagem)."""

import gzip
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import deque
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse, urlunparse
from xml.etree import ElementTree

HOSTS_PERMITIDOS = {"gralhaimoveis.com.br", "www.gralhaimoveis.com.br"}
ORIGEM = "https://www.gralhaimoveis.com.br"
AGENTE = "Mozilla/5.0 (compatible; ImoveisSite/1.0; +site de corretora parceira)"
TAMANHO_MAXIMO = 3_000_000
TEMPO_LIMITE = 20
MAX_REDIRECIONAMENTOS = 4

ANUNCIO = re.compile(r"^/imovel/venda\+[^/]+/\d+/?$")
LISTAGEM = re.compile(r"^/(?:$|venda(?:/|$)|bairro/|cidade/|imoveis(?:/|$)|busca|pesquisa)", re.I)


class Resposta:
    def __init__(self, tipo, texto="", url="", mensagem="", status=0):
        self.tipo = tipo  # "ok" | "sumiu" | "bloqueado" | "erro"
        self.texto = texto
        self.url = url
        self.mensagem = mensagem
        self.status = status


def validar_url(bruta: str, exigir_anuncio=True):
    """Aceita só HTTPS, host exato da allowlist, sem credenciais nem porta."""
    try:
        u = urlparse(bruta.strip())
    except ValueError:
        return None, "URL inválida."
    if u.scheme != "https":
        return None, "Só endereços https:// são aceitos."
    if u.username or u.password:
        return None, "URL com usuário/senha não é aceita."
    if u.port not in (None, 443):
        return None, "Porta não permitida."
    if (u.hostname or "").lower() not in HOSTS_PERMITIDOS:
        return None, "Endereço fora do site da Gralha Imóveis."
    if exigir_anuncio and not ANUNCIO.match(urllib.parse.unquote(u.path)):
        return None, "Não é um anúncio de venda individual (/imovel/venda+.../número)."
    limpa = urlunparse(("https", "www.gralhaimoveis.com.br", u.path, "", u.query if not exigir_anuncio else "", ""))
    return limpa, None


class _SemRedirecionar(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):  # tratamos redirecionamentos manualmente
        return None


_abridor = urllib.request.build_opener(_SemRedirecionar)


def baixar(url: str, tipos_aceitos=("text/html",), exigir_anuncio=False) -> Resposta:
    atual, erro = validar_url(url, exigir_anuncio=exigir_anuncio)
    if erro:
        return Resposta("bloqueado", mensagem=erro)
    for _ in range(MAX_REDIRECIONAMENTOS + 1):
        pedido = urllib.request.Request(atual, headers={
            "User-Agent": AGENTE,
            "Accept": "text/html,application/xml;q=0.9,*/*;q=0.5",
            "Accept-Encoding": "gzip",
        })
        try:
            r = _abridor.open(pedido, timeout=TEMPO_LIMITE)
            status, cabecalhos = r.status, r.headers
        except urllib.error.HTTPError as e:
            r, status, cabecalhos = e, e.code, e.headers
        except Exception as e:  # rede, DNS, tempo esgotado
            return Resposta("erro", mensagem=f"Falha de rede: {type(e).__name__}")

        if status in (301, 302, 303, 307, 308):
            destino = urljoin(atual, cabecalhos.get("Location", ""))
            proximo, erro = validar_url(destino, exigir_anuncio=False)
            if erro:
                return Resposta("bloqueado", mensagem="Redirecionamento para fora da Gralha bloqueado.")
            if exigir_anuncio and not ANUNCIO.match(urllib.parse.unquote(urlparse(proximo).path)):
                return Resposta("sumiu", mensagem="Anúncio redirecionado para outra página (provavelmente retirado).",
                                status=status)
            atual = proximo
            continue
        if status in (404, 410):
            return Resposta("sumiu", mensagem=f"A origem respondeu {status}.", status=status)
        if status != 200:
            return Resposta("erro", mensagem=f"A origem respondeu {status}.", status=status)

        tipo = (cabecalhos.get("Content-Type") or "").lower()
        if not any(t in tipo for t in tipos_aceitos):
            return Resposta("erro", mensagem=f"Conteúdo inesperado ({tipo or 'sem tipo'}).")
        corpo = r.read(TAMANHO_MAXIMO + 1)
        if len(corpo) > TAMANHO_MAXIMO:
            return Resposta("erro", mensagem="Página maior que o limite.")
        if (cabecalhos.get("Content-Encoding") or "").lower() == "gzip":
            corpo = gzip.decompress(corpo)
        return Resposta("ok", texto=corpo.decode("utf-8", errors="replace"), url=atual, status=200)
    return Resposta("erro", mensagem="Redirecionamentos demais.")


def normalizar_anuncio(href: str, base=ORIGEM):
    url = urljoin(base + "/", href)
    limpa, erro = validar_url(url, exigir_anuncio=True)
    return None if erro else limpa


class _Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            href = dict(attrs).get("href")
            if href:
                self.links.append(href)


def links_da_pagina(html: str):
    p = _Links()
    try:
        p.feed(html)
    except Exception:
        pass
    return p.links


def _locs(xml_texto: str):
    try:
        raiz = ElementTree.fromstring(xml_texto.encode("utf-8"))
    except ElementTree.ParseError:
        return [], []
    ns = re.match(r"\{.*\}", raiz.tag)
    ns = ns.group(0) if ns else ""
    locs = [e.text.strip() for e in raiz.iter(f"{ns}loc") if e.text]
    if raiz.tag.endswith("sitemapindex"):
        return [], locs
    return locs, []


def descobrir(baixar_fn=baixar, max_paginas=150, pausa=0.3, log=print, limite_segundos=360):
    """Encontra URLs de anúncios de venda. Devolve (urls, resumo)."""
    encontrados = {}
    resumo = {"sitemap": 0, "listagens": 0, "paginas_visitadas": 0, "falhas": {}}
    prazo = time.time() + limite_segundos

    # 1) Sitemap (e sitemaps filhos)
    fila_sm, vistos_sm = deque([ORIGEM + "/sitemap.xml"]), set()
    while fila_sm and len(vistos_sm) < 30:
        sm = fila_sm.popleft()
        if sm in vistos_sm:
            continue
        vistos_sm.add(sm)
        r = baixar_fn(sm, tipos_aceitos=("xml", "text/plain"))
        if r.tipo != "ok":
            log(f"  sitemap {sm}: {r.mensagem}")
            resumo["falhas"][urlparse(sm).path] = r.mensagem
            continue
        paginas, filhos = _locs(r.texto)
        fila_sm.extend(filhos)
        for loc in paginas:
            url = normalizar_anuncio(loc)
            if url and url not in encontrados:
                encontrados[url] = "sitemap"
                resumo["sitemap"] += 1

    # 2) Páginas de listagem do próprio site (complementa um sitemap desatualizado)
    fila, vistas = deque([ORIGEM + "/", ORIGEM + "/venda"]), set()
    while fila and len(vistas) < max_paginas and time.time() < prazo:
        pagina = fila.popleft()
        if pagina in vistas:
            continue
        vistas.add(pagina)
        r = baixar_fn(pagina)
        if r.tipo != "ok":
            if len(resumo["falhas"]) < 6:
                resumo["falhas"][urlparse(pagina).path or "/"] = r.mensagem
            continue
        for href in links_da_pagina(r.texto):
            anuncio = normalizar_anuncio(href, base=pagina.rstrip("/"))
            if anuncio:
                if anuncio not in encontrados:
                    encontrados[anuncio] = "listagem"
                    resumo["listagens"] += 1
                continue
            alvo = urljoin(pagina, href)
            u = urlparse(alvo)
            if (u.hostname or "").lower() in HOSTS_PERMITIDOS and LISTAGEM.match(u.path or "/"):
                proxima, erro = validar_url(alvo, exigir_anuncio=False)
                if not erro and proxima not in vistas:
                    fila.append(proxima)
        time.sleep(pausa)
    resumo["paginas_visitadas"] = len(vistas)
    return list(encontrados), resumo
