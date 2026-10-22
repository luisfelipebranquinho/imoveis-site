"""Gera o site completo em ./publicar a partir dos anúncios da Gralha Imóveis.

Uso:
    python -m gerador.build                 # busca tudo na origem e gera o site
    python -m gerador.build --amostra DIR   # usa arquivos HTML locais (testes)
"""

import argparse
import json
import os
import shutil
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path

from . import fonte, site, vrsync
from .extrator import extrair

RAIZ = Path(__file__).resolve().parent.parent
SAIDA = RAIZ / "publicar"
FUSO = timezone(timedelta(hours=-3))
CAMPOS_OBRIGATORIOS = ("nome", "email", "whatsapp", "site_url")


def log(msg):
    print(msg, flush=True)


def carregar_json(caminho, padrao):
    try:
        return json.loads(Path(caminho).read_text(encoding="utf-8"))
    except FileNotFoundError:
        return padrao


def carregar_config():
    cfg = carregar_json(RAIZ / "config.json", {})
    faltando = [c for c in CAMPOS_OBRIGATORIOS if not str(cfg.get(c, "")).strip()]
    if faltando:
        sys.exit(f"config.json: preencha {', '.join(faltando)}")
    if not cfg["site_url"].startswith("https://"):
        sys.exit("config.json: site_url precisa começar com https://")
    cfg["site_url"] = cfg["site_url"].rstrip("/")
    for lista in ("destaques", "lancamentos", "ocultar"):
        cfg[lista] = [str(c).strip() for c in cfg.get(lista, []) if str(c).strip()]
    return cfg


def links_extras():
    caminho = RAIZ / "imoveis-extras.txt"
    if not caminho.exists():
        return []
    urls = []
    for linha in caminho.read_text(encoding="utf-8").splitlines():
        linha = linha.strip()
        if linha and not linha.startswith("#"):
            limpa, erro = fonte.validar_url(linha)
            if erro:
                log(f"  imoveis-extras.txt ignorado ({erro}): {linha}")
            else:
                urls.append(limpa)
    return urls


def estado_anterior(cfg):
    """Lê o estado publicado na última execução (para confirmar remoções em 2 etapas)."""
    url = cfg["site_url"] + "/dados/estado.json"
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": fonte.AGENTE}),
                                    timeout=20) as r:
            dados = json.loads(r.read().decode("utf-8"))
            log(f"Estado anterior: {len(dados.get('imoveis', []))} imóveis")
            return dados
    except Exception as erro:
        log(f"Sem estado anterior ({type(erro).__name__}); começando do zero.")
        return {"imoveis": []}


def buscar_anuncios(urls, baixar_fn, pausa=0.25):
    def um(url):
        r = baixar_fn(url, exigir_anuncio=True)
        time.sleep(pausa)
        if r.tipo != "ok":
            return url, r.tipo, r.mensagem, None
        res = extrair(r.texto, url)
        if not res["ok"]:
            tipo = "sumiu" if res["motivo"] in ("nao-e-anuncio", "nao-e-venda") else "erro"
            return url, tipo, res["mensagem"], None
        return url, "ok", "", res["imovel"]

    with ThreadPoolExecutor(max_workers=3) as ex:
        return list(ex.map(um, urls))


def mesclar(cfg, anterior, resultados, agora_iso):
    """Junta o que veio da origem com o estado anterior e aplica as regras de remoção."""
    antigos = {p["url_origem"]: p for p in anterior.get("imoveis", [])}
    por_codigo, rel = {}, {"verificados": 0, "novos": 0, "atualizados": 0, "sem_mudanca": 0,
                           "aguardando_confirmacao": 0, "removidos": 0, "falhas": 0, "revisar": 0,
                           "detalhes": []}
    for url, tipo, msg, novo in resultados:
        rel["verificados"] += 1
        velho = antigos.get(url)
        if tipo == "ok":
            novo["primeira_vez"] = (velho or {}).get("primeira_vez", agora_iso)
            novo["verificado_em"] = agora_iso
            novo["ausencias"] = 0
            comparar = lambda d: {k: v for k, v in d.items()
                                  if k not in ("verificado_em", "ausencias", "primeira_vez", "atualizado_em",
                                               "destaque", "lancamento", "_ordem")}
            if not velho:
                rel["novos"] += 1
                novo["atualizado_em"] = agora_iso
            elif comparar(velho) != comparar(novo):
                rel["atualizados"] += 1
                novo["atualizado_em"] = agora_iso
            else:
                rel["sem_mudanca"] += 1
                novo["atualizado_em"] = velho.get("atualizado_em", agora_iso)
            if novo["revisar"]:
                rel["revisar"] += 1
                rel["detalhes"].append({"codigo": novo["codigo"], "revisar": novo["revisar"]})
            if novo["codigo"] in por_codigo:
                continue  # mesmo código em duas URLs: fica a primeira
            por_codigo[novo["codigo"]] = novo
        elif tipo == "sumiu" and velho:
            ausencias = velho.get("ausencias", 0) + 1
            if ausencias >= 2:
                rel["removidos"] += 1
                rel["detalhes"].append({"codigo": velho["codigo"], "removido": msg})
            else:
                rel["aguardando_confirmacao"] += 1
                por_codigo.setdefault(velho["codigo"], {**velho, "ausencias": ausencias})
        elif velho:  # erro temporário: mantém o que já estava publicado
            rel["falhas"] += 1
            rel["detalhes"].append({"codigo": velho["codigo"], "falha": msg})
            por_codigo.setdefault(velho["codigo"], velho)
        else:
            rel["falhas"] += 1 if tipo != "sumiu" else 0
            if tipo != "sumiu":
                rel["detalhes"].append({"url": url, "falha": msg})
    return list(por_codigo.values()), rel


def ordenar(cfg, imoveis):
    destaques = cfg["destaques"]
    for p in imoveis:
        p["destaque"] = p["codigo"] in destaques
        p["lancamento"] = p["codigo"] in cfg["lancamentos"]
    # Destaques na ordem do config; depois os demais, com foto primeiro e mais recentes antes.
    fixos = sorted((p for p in imoveis if p["destaque"]), key=lambda p: destaques.index(p["codigo"]))
    resto = sorted((p for p in imoveis if not p["destaque"]),
                   key=lambda p: p.get("primeira_vez", ""), reverse=True)
    resto.sort(key=lambda p: 0 if p["fotos"] else 1)  # sort estável: mantém a ordem por data
    final = fixos + resto
    for i, p in enumerate(final):
        p["_ordem"] = i
    return final


def semelhantes(p, todos, n=3):
    def pontos(q):
        return ((q["bairro"] == p["bairro"]) * 2 + (q["tipo"] == p["tipo"])
                - abs((q.get("preco") or 0) - (p.get("preco") or 0)) / max(p.get("preco") or 1, 1))
    candidatos = [q for q in todos if q["codigo"] != p["codigo"] and q["fotos"]]
    return sorted(candidatos, key=pontos, reverse=True)[:n]


def gerar_site(cfg, imoveis, rel_origem, saida=SAIDA, agora=None):
    agora = agora or datetime.now(timezone.utc)
    atualizado = agora.astimezone(FUSO).strftime("%d/%m/%Y às %H:%M")
    if saida.exists():
        shutil.rmtree(saida)
    (saida / "dados").mkdir(parents=True)
    shutil.copytree(RAIZ / "site" / "assets", saida / "assets")

    visiveis = [p for p in imoveis if p["codigo"] not in cfg["ocultar"]]
    visiveis = ordenar(cfg, visiveis)

    (saida / "index.html").write_text(site.pagina_inicial(cfg, visiveis, atualizado), encoding="utf-8")
    for p in visiveis:
        pasta = saida / "imovel" / p["codigo"]
        pasta.mkdir(parents=True, exist_ok=True)
        (pasta / "index.html").write_text(
            site.pagina_imovel(cfg, p, semelhantes(p, visiveis), atualizado), encoding="utf-8")
    (saida / "404.html").write_text(site.pagina_404(cfg), encoding="utf-8")
    (saida / ".nojekyll").write_text("", encoding="utf-8")

    # Feeds VRSync: geral + segmentados ativos (pausados não são gerados -> 404)
    relatorio_feeds = {}
    xml, rel = vrsync.gerar(cfg, visiveis, None, agora)
    (saida / "vrsync.xml").write_text(xml, encoding="utf-8")
    relatorio_feeds["vrsync.xml"] = rel
    for feed in carregar_json(RAIZ / "feeds.json", []):
        slug_feed = str(feed.get("slug", "")).strip().lower()
        if not slug_feed or not all(c.isalnum() or c == "-" for c in slug_feed):
            log(f"  feed ignorado (slug inválido): {feed.get('nome')}")
            continue
        if not feed.get("ativo", True):
            relatorio_feeds[f"vrsync/{slug_feed}.xml"] = "pausado"
            continue
        xml, rel = vrsync.gerar(cfg, visiveis, feed, agora)
        (saida / "vrsync").mkdir(exist_ok=True)
        (saida / "vrsync" / f"{slug_feed}.xml").write_text(xml, encoding="utf-8")
        relatorio_feeds[f"vrsync/{slug_feed}.xml"] = rel

    # Mapa do site e robots
    urls = [cfg["site_url"] + "/"] + [f"{cfg['site_url']}/imovel/{p['codigo']}/" for p in visiveis]
    mapa = "".join(f"<url><loc>{vrsync.esc(u)}</loc></url>" for u in urls)
    (saida / "sitemap.xml").write_text(
        f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{mapa}</urlset>',
        encoding="utf-8")
    (saida / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {cfg['site_url']}/sitemap.xml\n",
                                      encoding="utf-8")

    estado = {"gerado_em": agora.isoformat(), "imoveis": imoveis}
    (saida / "dados" / "estado.json").write_text(json.dumps(estado, ensure_ascii=False), encoding="utf-8")
    relatorio = {"gerado_em": agora.astimezone(FUSO).isoformat(), "no_site": len(visiveis),
                 "origem": rel_origem, "feeds": relatorio_feeds}
    (saida / "dados" / "relatorio.json").write_text(json.dumps(relatorio, ensure_ascii=False, indent=2),
                                                    encoding="utf-8")
    return relatorio


def resumo_markdown(rel):
    o = rel["origem"]
    linhas = [
        "## Atualização do site de imóveis", "",
        f"- Imóveis no site: **{rel['no_site']}**",
        f"- Verificados na Gralha: {o.get('verificados', 0)} (novos {o.get('novos', 0)}, "
        f"atualizados {o.get('atualizados', 0)}, sem mudança {o.get('sem_mudanca', 0)})",
        f"- Removidos (confirmado 2x): {o.get('removidos', 0)} · aguardando confirmação: "
        f"{o.get('aguardando_confirmacao', 0)}",
        f"- Falhas temporárias: {o.get('falhas', 0)} · para revisar: {o.get('revisar', 0)}",
        "", "| Feed | Exportados | Rejeitados | Sem endereço | Sem foto | Sem preço | Sem área |",
        "|---|---|---|---|---|---|---|",
    ]
    for nome, r in rel["feeds"].items():
        if r == "pausado":
            linhas.append(f"| {nome} | pausado | | | | | |")
        else:
            linhas.append(f"| {nome} | {r['exportados']} | {r['rejeitados']} | {r['sem_endereco']} | "
                          f"{r['sem_foto']} | {r['sem_preco']} | {r['sem_area']} |")
    return "\n".join(linhas) + "\n"


def principal():
    ap = argparse.ArgumentParser()
    ap.add_argument("--amostra", help="pasta com arquivos .html de anúncios (modo de teste, sem internet)")
    args = ap.parse_args()
    cfg = carregar_config()
    agora = datetime.now(timezone.utc)
    agora_iso = agora.astimezone(FUSO).isoformat(timespec="seconds")

    if args.amostra:
        pasta = Path(args.amostra)
        resultados = []
        for arq in sorted(pasta.glob("*.html")):
            url = arq.with_suffix(".url").read_text(encoding="utf-8").strip()
            res = extrair(arq.read_text(encoding="utf-8"), url)
            resultados.append((url, "ok", "", res["imovel"]) if res["ok"] else (url, "erro", res["mensagem"], None))
        anterior = {"imoveis": []}
        resumo_desc = {"modo": "amostra"}
    else:
        anterior = estado_anterior(cfg)
        log("Procurando anúncios de venda na Gralha Imóveis...")
        urls, resumo_desc = fonte.descobrir(log=log)
        log(f"  encontrados: {len(urls)} ({resumo_desc})")
        conhecidos = [p["url_origem"] for p in anterior.get("imoveis", [])]
        todos = list(dict.fromkeys(urls + links_extras() + conhecidos))
        log(f"Lendo {len(todos)} anúncios...")
        resultados = buscar_anuncios(todos, fonte.baixar)

    imoveis, rel_origem = mesclar(cfg, anterior, resultados, agora_iso)
    rel_origem["descoberta"] = resumo_desc

    # Trava de segurança: se a origem falhar em massa, não apaga o site publicado.
    qtd_anterior = len(anterior.get("imoveis", []))
    if not imoveis:
        sys.exit("Nenhum imóvel lido. O site publicado foi mantido como estava.")
    if qtd_anterior >= 10 and len(imoveis) < qtd_anterior * 0.5 and not os.environ.get("FORCAR"):
        sys.exit(f"Queda brusca ({qtd_anterior} -> {len(imoveis)} imóveis). Publicação cancelada por segurança; "
                 "rode manualmente com 'forçar' se for esperado.")

    rel = gerar_site(cfg, imoveis, rel_origem, agora=agora)
    texto = resumo_markdown(rel)
    log(texto)
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as f:
            f.write(texto)


if __name__ == "__main__":
    principal()
