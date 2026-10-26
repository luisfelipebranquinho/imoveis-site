"""Leitura de um anúncio público da Gralha Imóveis (HTML gerado no servidor).

Estratégia em camadas: metadados (Open Graph) quando existem, HTML como base,
URL apenas para conferência. O código oficial do anúncio prevalece sobre o
identificador técnico da URL.
"""

import re
from urllib.parse import unquote, urlparse

from bs4 import BeautifulSoup

from .textos import chave, dinheiro, limpar, numero_br

# Características aceitas (chave sem acento -> rótulo exibido). O que não estiver
# aqui é descartado e contado no relatório como "característica removida".
CARACTERISTICAS = {
    "area servico": "Área de serviço",
    "area de servico": "Área de serviço",
    "cozinha americana": "Cozinha americana",
    "cozinha": "Cozinha",
    "copa cozinha": "Copa-cozinha",
    "lavabo": "Lavabo",
    "living": "Living",
    "sala de estar": "Sala de estar",
    "sala de jantar": "Sala de jantar",
    "vista mar": "Vista para o mar",
    "vista para o mar": "Vista para o mar",
    "vista panoramica": "Vista panorâmica",
    "churrasqueira": "Churrasqueira",
    "piscina": "Piscina",
    "piscina infantil": "Piscina infantil",
    "piscina privativa": "Piscina privativa",
    "elevador": "Elevador",
    "sacada": "Sacada",
    "varanda": "Varanda",
    "varanda gourmet": "Varanda gourmet",
    "terraco": "Terraço",
    "ar condicionado": "Ar-condicionado",
    "mobiliado": "Mobiliado",
    "semi mobiliado": "Semimobiliado",
    "semimobiliado": "Semimobiliado",
    "portaria": "Portaria",
    "portaria 24h": "Portaria 24h",
    "portaria 24 horas": "Portaria 24h",
    "porteiro eletronico": "Porteiro eletrônico",
    "interfone": "Interfone",
    "zelador": "Zelador",
    "academia": "Academia",
    "sala fitness": "Academia",
    "salao de festas": "Salão de festas",
    "salao festas": "Salão de festas",
    "salao de jogos": "Salão de jogos",
    "salao jogos": "Salão de jogos",
    "sala de jogos": "Sala de jogos",
    "playground": "Playground",
    "brinquedoteca": "Brinquedoteca",
    "sauna": "Sauna",
    "spa": "Spa",
    "hidromassagem": "Hidromassagem",
    "quadra": "Quadra esportiva",
    "quadra poliesportiva": "Quadra esportiva",
    "jardim": "Jardim",
    "quintal": "Quintal",
    "closet": "Closet",
    "escritorio": "Escritório",
    "home office": "Home office",
    "despensa": "Despensa",
    "lareira": "Lareira",
    "lavanderia": "Lavanderia",
    "gas encanado": "Gás encanado",
    "bicicletario": "Bicicletário",
    "coworking": "Coworking",
    "espaco gourmet": "Espaço gourmet",
    "area de lazer": "Área de lazer",
    "armarios embutidos": "Armários embutidos",
    "armario embutido": "Armários embutidos",
    "cerca eletrica": "Cerca elétrica",
    "alarme": "Alarme",
    "energia solar": "Energia solar",
    "aquecimento": "Aquecimento",
    "aquecimento a gas": "Aquecimento a gás",
    "aquecimento solar": "Aquecimento solar",
    "aquecimento central": "Aquecimento central",
    "agua quente": "Água quente",
    "espera split": "Infraestrutura para ar-condicionado",
    "estacionamento": "Estacionamento",
    "quiosque": "Quiosque",
    "pet place": "Pet place",
    "gerador": "Gerador",
    "cinema": "Cinema",
    "banheiro social": "Banheiro social",
}

TIPOS = {
    "apartamento": "apartamento",
    "casa": "casa",
    "casa-em-condominio": "casa-em-condominio",
    "sobrado": "sobrado",
    "cobertura": "cobertura",
    "estudio": "studio",
    "studio": "studio",
    "kitnet": "kitnet",
    "loft": "loft",
    "terreno": "terreno",
    "lote": "terreno",
    "sala": "sala",
    "sala-comercial": "sala",
    "loja": "loja",
    "galpao": "galpao",
    "sitio": "sitio",
    "chacara": "sitio",
    "fazenda": "fazenda",
}

_FOTO = re.compile(r"https?://[^\s\"'()<>\\]+/api/image/\d+\.(?:jpe?g|png|webp)", re.I)


def _normalizar_caracteristicas(itens):
    mantidas, removidas = [], 0
    for bruto in itens:
        rotulo = CARACTERISTICAS.get(chave(bruto))
        if rotulo:
            if rotulo not in mantidas:
                mantidas.append(rotulo)
        elif chave(bruto):
            removidas += 1
    return mantidas, removidas


def _tipo(bruto):
    if not bruto:
        return None
    return TIPOS.get(chave(bruto).replace(" ", "-"))


def _separar_numero(endereco):
    m = re.match(r"^(.+?)(?:,\s*|\s+n[º°o.]*\s*|\s+-\s+)(\d{1,5}[A-Za-z]?)$", endereco, re.I)
    if m:
        return limpar(m.group(1)), m.group(2)
    return limpar(endereco), None


def _texto_com_quebras(el):
    for br in el.find_all("br"):
        br.replace_with("\n")
    for tag in el.find_all(["script", "style", "iframe"]):
        tag.decompose()
    linhas = [limpar(l) for l in el.get_text().split("\n")]
    texto = "\n".join(linhas)
    return re.sub(r"\n{3,}", "\n\n", texto).strip()


def id_tecnico(url):
    partes = [p for p in urlparse(url).path.split("/") if p]
    return partes[-1] if partes and partes[-1].isdigit() else None


def extrair(html: str, url: str) -> dict:
    """Devolve {"ok": True, "imovel": {...}} ou {"ok": False, "motivo", "mensagem"}."""
    sopa = BeautifulSoup(html, "html.parser")
    notas = []

    if not sopa.select_one(".Page_DetailProperty"):
        return {"ok": False, "motivo": "nao-e-anuncio",
                "mensagem": "A página não tem a estrutura de um anúncio de imóvel."}

    partes = [p for p in urlparse(url).path.split("/") if p]
    tokens = unquote(partes[1]).split("+") if len(partes) > 1 else []

    texto_valores = limpar(sopa.select_one(".Page_DetailProperty_Values").get_text(" ")
                           if sopa.select_one(".Page_DetailProperty_Values") else "")
    if (tokens[:1] != ["venda"]) and not re.search(r"valor de venda", texto_valores, re.I):
        return {"ok": False, "motivo": "nao-e-venda",
                "mensagem": "O anúncio não é de venda."}

    # Código oficial
    codigo = None
    for el in sopa.select(".DetailProperty_Header_Tags .Tag_Content_Label"):
        m = re.search(r"c[óo]d(?:igo)?\.?:?\s*([A-Za-z0-9._-]+)", limpar(el.get_text()), re.I)
        if m:
            codigo = m.group(1)
            break
    if not codigo:
        migalha = sopa.select_one(".Breadcrumb_Item.__is-actual")
        m = re.search(r"(\d{3,})\s*$", limpar(migalha.get_text(" ")) if migalha else "")
        if m:
            codigo = m.group(1)
    if not codigo:
        return {"ok": False, "motivo": "sem-codigo",
                "mensagem": "Código oficial do imóvel não encontrado."}

    # Título, sem preço nem assinatura da origem
    h1 = sopa.select_one(".Page_DetailProperty_Title h1")
    titulo = limpar(h1.get_text(" ")) if h1 else ""
    if not titulo:
        og = sopa.select_one('meta[property="og:title"]')
        titulo = limpar(og.get("content", "")) if og else ""
    titulo = re.sub(r"\s+por R\$\s*[\d.,]+", "", titulo, flags=re.I)
    titulo = re.sub(r"\s*[-–|]\s*Gralha Im[óo]veis\s*$", "", titulo, flags=re.I).strip()
    if not titulo:
        return {"ok": False, "motivo": "sem-titulo", "mensagem": "Título não encontrado."}

    # Preço, conferido com o valor presente na URL
    span = sopa.select_one(".Page_DetailProperty_Values h1 span")
    preco = dinheiro(span.get_text(" ") if span else "") or dinheiro(texto_valores)
    token_preco = next((t for t in tokens if re.match(r"^rs\d", t)), None)
    if token_preco:
        preco_url = numero_br(token_preco[2:])
        if preco is None and preco_url:
            preco = preco_url
            notas.append("Preço lido da URL (não estava na página).")
        elif preco is not None and preco_url and abs(preco_url - preco) > 1:
            notas.append(f"Preço da página ({preco:.0f}) diferente do preço da URL ({preco_url:.0f}).")
    if preco is not None and preco <= 0:
        preco = None
    if preco is None:
        notas.append("Preço não encontrado.")

    conteudo = sopa.select_one(".Page_DetailProperty_Content")
    texto_detalhes = limpar(conteudo.get_text(" ")) if conteudo else texto_valores
    condominio = iptu = periodo_iptu = None
    m = re.search(r"condom[ií]nio:?\s*R\$\s*(\d[\d.]*(?:,\d{1,2})?)", texto_detalhes, re.I)
    if m:
        condominio = numero_br(m.group(1))
    m = re.search(r"IPTU:?\s*R\$\s*(\d[\d.]*(?:,\d{1,2})?)\s*(/\s*m[eê]s|/\s*ano|mensal|anual)?",
                  texto_detalhes, re.I)
    if m:
        iptu = numero_br(m.group(1))
        p = (m.group(2) or "").lower()
        if "m" in p:
            periodo_iptu = "Monthly"
        elif p:
            periodo_iptu = "Yearly"
        else:
            notas.append("IPTU sem periodicidade; não vai para o feed.")

    # Tipo: migalha (/venda/casa) -> URL -> primeira palavra do título
    tipo = None
    for a in sopa.select(".Breadcrumb a[href]"):
        m = re.match(r"^/venda/([a-z0-9-]+)/?$", a["href"], re.I)
        if m:
            tipo = _tipo(m.group(1)) or tipo
    tipo = tipo or _tipo(tokens[1] if len(tokens) > 1 else "") or _tipo(titulo.split(" ")[0])
    if not tipo:
        tipo = chave(tokens[1] if len(tokens) > 1 else "desconhecido").replace(" ", "-")
        notas.append(f'Tipo "{tipo}" sem correspondência no padrão dos portais.')

    # Localização
    rotulo = sopa.select_one(".DetailProperty_Address_Label")
    if rotulo:
        for a in rotulo.find_all("a"):
            a.decompose()
    partes_loc = [limpar(p) for p in limpar(rotulo.get_text(" ") if rotulo else "").split(",")]
    bairro_bruto = partes_loc[0] if partes_loc else ""
    cidade = partes_loc[1] if len(partes_loc) > 1 else ""
    uf = partes_loc[2].upper()[:2] if len(partes_loc) > 2 else ""
    bairro = bairro_bruto
    if cidade and bairro.lower() != cidade.lower() and bairro.lower().endswith(" " + cidade.lower()):
        bairro = bairro[: -len(cidade)].strip()
    if not (bairro and cidade and uf):
        notas.append("Localização incompleta.")

    endereco = numero = None
    for p in sopa.find_all("p"):
        m = re.match(r"^Endere[çc]o:\s*(.+)$", limpar(p.get_text(" ")), re.I)
        if m:
            endereco, numero = _separar_numero(m.group(1))
            break
    if not endereco:
        notas.append("Endereço (rua) não informado na origem.")

    # Área, quartos, banheiros, vagas
    area = quartos = suites = banheiros = vagas = None
    for li in sopa.select(".DetailProperty_Features_Item"):
        img = li.find("img")
        alt = chave(img.get("alt", "")) if img else ""
        rot = li.select_one(".Features_Item_Label")
        txt = limpar(rot.get_text(" ") if rot else li.get_text(" "))
        n = re.search(r"(\d+)", txt)
        if "area" in alt:
            m = re.search(r"(\d[\d.]*(?:,\d+)?)\s*m", txt, re.I)
            if m and area is None:
                area = numero_br(m.group(1))
        elif "quarto" in alt or "dormit" in alt:
            if n:
                quartos = int(n.group(1))
            s = re.search(r"(\d+)\s*su[ií]tes?", txt, re.I)
            if s:
                suites = int(s.group(1))
        elif "banheiro" in alt:
            banheiros = int(n.group(1)) if n else None
        elif "garag" in alt or "vaga" in alt:
            vagas = int(n.group(1)) if n else None
    if area is None:
        notas.append("Área não encontrada.")

    # Descrição
    descricao = None
    for sec in sopa.select(".Page_DetailProperty_About"):
        t = sec.select_one(".DetailProperty_About_Title")
        if t and "sobre" in chave(t.get_text()):
            corpo = sec.select_one(".DetailProperty_About_Text")
            if corpo:
                descricao = _texto_com_quebras(corpo)[:8000] or None
            break
    if not descricao:
        meta = sopa.select_one('meta[name="description"]')
        if meta and limpar(meta.get("content")):
            descricao = limpar(meta.get("content"))
            notas.append("Descrição curta: só havia o resumo da página.")

    # Infraestrutura do imóvel e do condomínio
    do_imovel, do_condominio = [], []
    for sec in sopa.select(".Page_DetailProperty_Facilities"):
        t = sec.select_one(".DetailProperty_Facilities_Title")
        itens = [limpar(li.get_text(" ")) for li in sec.find_all("li")]
        itens = [i for i in itens if i]
        (do_condominio if t and "condominio" in chave(t.get_text()) else do_imovel).extend(itens)
    caract, rem1 = _normalizar_caracteristicas(do_imovel)
    caract_cond, rem2 = _normalizar_caracteristicas(do_condominio)

    # Fotos: capa (og:image) primeiro, depois a galeria na ordem; só HTTPS e sem repetir
    og_img = sopa.select_one('meta[property="og:image"]')
    capa = limpar(og_img.get("content", "")) if og_img else ""
    capa = re.sub(r"^http://", "https://", capa, flags=re.I)
    if not _FOTO.fullmatch(capa):  # a origem às vezes publica a capa sem o número da foto (".../image/.jpg")
        capa = ""
    galeria = {re.sub(r"^http://", "https://", u, flags=re.I) for u in _FOTO.findall(html)}

    def id_foto(u):
        m = re.search(r"/api/image/(\d+)\.", u)
        return int(m.group(1)) if m else 0

    fotos = []
    for u in [capa, *sorted(galeria, key=id_foto)]:
        if u.startswith("https://") and u not in fotos:
            fotos.append(u)
    if not fotos:
        notas.append("Nenhuma foto encontrada.")

    video = None
    iframe = sopa.select_one("iframe[src*='youtube.com/embed']")
    if iframe:
        video = re.sub(r"^//", "https://", limpar(iframe.get("src")))
        if not video.startswith("https://www.youtube.com/embed/"):
            video = None

    return {
        "ok": True,
        "imovel": {
            "codigo": codigo,
            "url_origem": url,
            "id_tecnico": id_tecnico(url),
            "titulo": titulo,
            "tipo": tipo,
            "bairro": bairro,
            "cidade": cidade,
            "uf": uf,
            "endereco": endereco,
            "numero": numero,
            "preco": preco,
            "condominio": condominio,
            "iptu": iptu,
            "periodo_iptu": periodo_iptu,
            "area": area,
            "quartos": quartos,
            "suites": suites,
            "banheiros": banheiros,
            "vagas": vagas,
            "descricao": descricao,
            "caracteristicas": caract,
            "caracteristicas_condominio": caract_cond,
            "caracteristicas_removidas": rem1 + rem2,
            "fotos": fotos,
            "video": video,
            "revisar": notas,
        },
    }
