"""Geração do XML no padrão VRSync (Viva Real / ZAP)."""

from datetime import datetime, timedelta, timezone
from xml.etree import ElementTree

from .textos import chave, inteiro_ou_decimal, limpar

# Tabela de correspondência tipo -> padrão VRSync. Ajuste aqui se o portal pedir outro valor.
TIPOS_VRSYNC = {
    "apartamento": ("Residential / Apartment", "Residential", "LivingArea"),
    "casa": ("Residential / Home", "Residential", "LivingArea"),
    "casa-em-condominio": ("Residential / Condo", "Residential", "LivingArea"),
    "sobrado": ("Residential / Sobrado", "Residential", "LivingArea"),
    "cobertura": ("Residential / Penthouse", "Residential", "LivingArea"),
    "studio": ("Residential / Studio", "Residential", "LivingArea"),
    "loft": ("Residential / Studio", "Residential", "LivingArea"),
    "kitnet": ("Residential / Kitnet", "Residential", "LivingArea"),
    "terreno": ("Residential / Land Lot", "Residential", "LotArea"),
    "sitio": ("Residential / Farm Ranch", "Residential", "LotArea"),
    "fazenda": ("Residential / Farm Ranch", "Residential", "LotArea"),
    "sala": ("Commercial / Office", "Commercial", "LivingArea"),
    "loja": ("Commercial / Business", "Commercial", "LivingArea"),
    "galpao": ("Commercial / Industrial", "Commercial", "LivingArea"),
}

ESTADOS = {
    "AC": "Acre", "AL": "Alagoas", "AP": "Amapá", "AM": "Amazonas", "BA": "Bahia", "CE": "Ceará",
    "DF": "Distrito Federal", "ES": "Espírito Santo", "GO": "Goiás", "MA": "Maranhão",
    "MT": "Mato Grosso", "MS": "Mato Grosso do Sul", "MG": "Minas Gerais", "PA": "Pará",
    "PB": "Paraíba", "PR": "Paraná", "PE": "Pernambuco", "PI": "Piauí", "RJ": "Rio de Janeiro",
    "RN": "Rio Grande do Norte", "RS": "Rio Grande do Sul", "RO": "Rondônia", "RR": "Roraima",
    "SC": "Santa Catarina", "SP": "São Paulo", "SE": "Sergipe", "TO": "Tocantins",
}


def esc(s) -> str:
    return (limpar(str(s)).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            .replace('"', "&quot;").replace("'", "&apos;"))


def cdata(s: str) -> str:
    texto = "\n".join(limpar(l) for l in str(s).split("\n"))
    return "<![CDATA[" + texto.replace("]]>", "]]]]><![CDATA[>") + "]]>"


def num(n) -> str:
    return str(inteiro_ou_decimal(n))


def motivo_rejeicao(p: dict):
    if p["tipo"] not in TIPOS_VRSYNC:
        return "tipo_sem_mapeamento"
    if not p.get("preco") or p["preco"] <= 0:
        return "sem_preco"
    if not any(u.startswith("https://") for u in p.get("fotos", [])):
        return "sem_foto"
    if not (p.get("endereco") or "").strip():
        return "sem_endereco"
    if not p.get("area") or p["area"] <= 0:
        return "sem_area"
    return None


def atende_filtros(feed: dict | None, p: dict) -> bool:
    if not feed:
        return True
    codigo = p["codigo"]
    if codigo in feed.get("excluir_codigos", []):
        return False
    if feed.get("selecao") == "manual":
        return codigo in feed.get("incluir_codigos", [])
    preco = p.get("preco")
    if feed.get("preco_minimo") is not None and (preco is None or preco < feed["preco_minimo"]):
        return False
    if feed.get("preco_maximo") is not None and (preco is None or preco > feed["preco_maximo"]):
        return False
    bairros = [chave(b) for b in feed.get("bairros", [])]
    if bairros and chave(p["bairro"]) not in bairros:
        return False
    tipos = [chave(t) for t in feed.get("tipos", [])]
    if tipos and chave(p["tipo"]) not in tipos:
        return False
    if feed.get("somente_destaques") and not p.get("destaque"):
        return False
    if feed.get("somente_lancamentos") and not p.get("lancamento"):
        return False
    return True


def _anuncio(p: dict, cfg: dict) -> str:
    tipo_vr, uso, campo_area = TIPOS_VRSYNC[p["tipo"]]
    base = cfg["site_url"].rstrip("/")
    fotos = list(dict.fromkeys(u for u in p["fotos"] if u.startswith("https://")))
    publicacao = "PREMIUM" if p.get("destaque") and cfg.get("permitir_premium") else "STANDARD"
    pagina = base + "/imovel/" + p["codigo"] + "/"
    o = ["    <Listing>",
         f"      <ListingID>{esc(p['codigo'])}</ListingID>",
         f"      <Title>{cdata(p['titulo'])}</Title>",
         "      <TransactionType>For Sale</TransactionType>",
         f"      <PublicationType>{publicacao}</PublicationType>",
         f"      <DetailViewUrl>{esc(pagina)}</DetailViewUrl>",
         "      <Media>"]
    for i, u in enumerate(fotos):
        legenda = "Principal" if i == 0 else f"Foto {i + 1}"
        primaria = ' primary="true"' if i == 0 else ""
        o.append(f'        <Item medium="image" caption="{legenda}"{primaria}>{esc(u)}</Item>')
    o += ["      </Media>", "      <Details>", f"        <PropertyType>{esc(tipo_vr)}</PropertyType>"]
    if p.get("descricao"):
        o.append(f"        <Description>{cdata(p['descricao'])}</Description>")
    o.append(f'        <ListPrice currency="BRL">{num(p["preco"])}</ListPrice>')
    if p.get("condominio") is not None and p["condominio"] > 0:
        o.append(f'        <PropertyAdministrationFee currency="BRL">{num(p["condominio"])}</PropertyAdministrationFee>')
    # IPTU só sai com periodicidade conhecida (não convertemos mensal em anual).
    if p.get("iptu") and p.get("periodo_iptu") in ("Monthly", "Yearly"):
        o.append(f'        <Iptu currency="BRL" period="{p["periodo_iptu"]}">{num(p["iptu"])}</Iptu>')
    o.append(f'        <{campo_area} unit="square metres">{num(p["area"])}</{campo_area}>')
    comodos = ""
    if campo_area == "LivingArea":
        for campo, tag in (("quartos", "Bedrooms"), ("suites", "Suites"),
                           ("banheiros", "Bathrooms"), ("vagas", "Garage")):
            if p.get(campo) is not None:
                comodos += f"<{tag}>{p[campo]}</{tag}>"
    elif p.get("vagas") is not None:
        comodos = f"<Garage>{p['vagas']}</Garage>"
    if comodos:
        o.append("        " + comodos)
    o.append(f"        <UsageType>{uso}</UsageType>")
    caract = list(dict.fromkeys(p.get("caracteristicas", []) + p.get("caracteristicas_condominio", [])))
    if caract:
        o.append("        <Features>" + "".join(f"<Feature>{esc(c)}</Feature>" for c in caract) + "</Features>")
    uf = p["uf"].upper()
    o += ["      </Details>",
          f'      <Location displayAddress="{esc(cfg.get("exibir_endereco", "Street"))}">',
          '        <Country abbreviation="BR">Brasil</Country>',
          f'        <State abbreviation="{esc(uf)}">{esc(ESTADOS.get(uf, uf))}</State>',
          f"        <City>{esc(p['cidade'])}</City>",
          f"        <Neighborhood>{esc(p['bairro'])}</Neighborhood>",
          f"        <Address>{esc(p['endereco'])}</Address>"]
    if p.get("numero"):
        o.append(f"        <StreetNumber>{esc(p['numero'])}</StreetNumber>")
    o += ["      </Location>", "    </Listing>"]
    return "\n".join(o)


def gerar(cfg: dict, imoveis: list[dict], feed: dict | None = None, agora: datetime | None = None):
    """Devolve (xml, relatorio). Lança ValueError se o XML gerado não for bem-formado."""
    rel = {"elegiveis": 0, "exportados": 0, "rejeitados": 0, "sem_endereco": 0, "sem_descricao": 0,
           "sem_preco": 0, "sem_area": 0, "sem_foto": 0, "tipo_sem_mapeamento": 0, "duplicados": 0,
           "caracteristicas_removidas": 0, "rejeitados_codigos": []}
    vistos, blocos = set(), []
    for p in imoveis:
        if not atende_filtros(feed, p):
            continue
        rel["elegiveis"] += 1
        rel["caracteristicas_removidas"] += p.get("caracteristicas_removidas", 0)
        if not p.get("descricao"):
            rel["sem_descricao"] += 1
        motivo = "duplicados" if p["codigo"] in vistos else motivo_rejeicao(p)
        if motivo:
            rel[motivo] += 1
            rel["rejeitados"] += 1
            rel["rejeitados_codigos"].append({"codigo": p["codigo"], "motivo": motivo})
            continue
        vistos.add(p["codigo"])
        blocos.append(_anuncio(p, cfg))
    rel["exportados"] = len(blocos)

    agora = agora or datetime.now(timezone.utc)
    brt = agora.astimezone(timezone(timedelta(hours=-3))).strftime("%Y-%m-%dT%H:%M:%S-03:00")
    xml = "\n".join([
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<ListingDataFeed xmlns="http://www.vivareal.com/schemas/1.0/VRSync" '
        'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
        'xsi:schemaLocation="http://www.vivareal.com/schemas/1.0/VRSync http://xml.vivareal.com/vrsync.xsd">',
        "  <Header>",
        f"    <Provider>{esc(cfg['nome'])}</Provider>",
        f"    <Email>{esc(cfg['email'])}</Email>",
        f"    <ContactName>{esc(cfg.get('responsavel') or cfg['nome'])}</ContactName>",
        f"    <PublishDate>{brt}</PublishDate>",
        f"    <Telephone>{esc(cfg.get('telefone') or cfg.get('whatsapp', ''))}</Telephone>",
        "  </Header>",
        "  <Listings>",
        *blocos,
        "  </Listings>",
        "</ListingDataFeed>",
        "",
    ])
    ElementTree.fromstring(xml.encode("utf-8"))  # valida: lança ParseError se malformado
    return xml, rel
