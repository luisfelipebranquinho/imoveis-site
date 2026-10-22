"""Cria páginas de exemplo no mesmo formato dos anúncios da Gralha Imóveis.

O formato foi copiado de anúncios reais (estrutura de classes, rótulos e URLs),
com dados inventados. Rodar: python tests/criar_amostras.py
"""

from pathlib import Path

PASTA = Path(__file__).parent / "amostras"

MODELO = """<!DOCTYPE html><html lang="pt-BR"><head><meta charset="utf-8" />
<meta name="description" content="{resumo}" />
<meta property="og:site_name" content="Gralha Imóveis" />
<meta property="og:image" content="http://gralha2.inforcedata.com.br/api/image/{foto0}.jpg" />
<meta property="og:title" content="{og_titulo} - Gralha Imóveis" />
<title>{og_titulo} - Gralha Imóveis</title></head><body>
<section class="Page Page_DetailProperty __is-active"><nav class="Page_NavHeader"><ul class="Breadcrumb">
<li class="Breadcrumb_Item"><a href="/">Início</a></li><li class="Breadcrumb_Item"><a href="/venda">imóveis</a></li>
<li class="Breadcrumb_Item"><a href="/venda/{tipo}">{tipo}</a></li>
<li class="Breadcrumb_Item __is-actual">
					{bairro_completo}
					-
						{quartos}
						domitórios(s)
					-
					{codigo}
				</li></ul></nav>
<div class="InternaGaleria"><div class="InternaGaleria_Full">{galeria}</div></div>
<div class="Page_Content"><div class="Page_DetailProperty_Content">
<div class="Page_DetailProperty_Header"><div class="DetailProperty_Header_Tags">
<a class="Tag"><div class="Tag_Content"><div class="Tag_Content_Label"> Oportunidade </div></div></a>
<div class="Tag"><div class="Tag_Content"><div class="Tag_Content_Label"> Cod: {codigo} </div></div></div></div></div>
<div class="Page_DetailProperty_Title"><h1>{h1}</h1></div>
<div class="Page_DetailProperty_Values"><h1> Valor de venda: <span> R$ {preco_txt} </span></h1><h1>{taxas}</h1></div>
<div class="Page_DetailProperty_Address"><div class="DetailProperty_Address_Label"> {bairro_completo}, {cidade}, SC <a href="#Mapa" class="scrollLink">VER NO MAPA</a></div></div>
<div class="Page_DetailProperty_Features"><ul>
<li class="DetailProperty_Features_Item"><div class="Features_Item_Icon"><img src="/x/focus.svg" alt="area util"></div><div class="Features_Item_Label"><span>{area}m²</span></div></li>
<li class="DetailProperty_Features_Item"><div class="Features_Item_Icon"><img src="/x/bed.svg" alt="quartos"></div><div class="Features_Item_Label"><span> {quartos} dormitórios ({suites} suítes) </span></div></li>
<li class="DetailProperty_Features_Item"><div class="Features_Item_Icon"><img src="/x/shower.svg" alt="banheiros"></div><div class="Features_Item_Label"><span> {banheiros} banheiros </span></div></li>
<li class="DetailProperty_Features_Item"><div class="Features_Item_Icon"><img src="/x/garage.svg" alt="garagem"></div><div class="Features_Item_Label"><span> {vagas} vagas </span></div></li>
</ul></div>
<div class="Page_DetailProperty_About"><div class="DetailProperty_About_Title"><h3>Sobre este imóvel</h3></div>
<div class="DetailProperty_About_Text"><p> {descricao} </p></div></div>
<div class="Page_DetailProperty_Facilities"><div class="DetailProperty_Facilities_Title"><h3>Infraestrutura do Imóvel</h3></div>
<div class="DetailProperty_Facilities_List"><ul>{itens}</ul></div></div>
<div class="Page_DetailProperty_Facilities"><div class="DetailProperty_Facilities_Title"><h3>Infraestrutura do Condomínio</h3></div>
<div class="DetailProperty_Facilities_List"><ul>{itens_cond}</ul></div></div>
<div class="Page_DetailProperty_About"><div class="DetailProperty_About_Title"><h3>Localização do Imóvel</h3></div>
<div class="DetailProperty_About_Text"><p>Bairro: <b>{bairro_completo}</b> - {cidade}, SC</p>{endereco}</div></div>
</div></div></section></body></html>"""

AMOSTRAS = [
    dict(codigo="32819", id="165130823", tipo="casa", bairro_completo="Centro Florianópolis", cidade="Florianópolis",
         quartos=4, suites=3, banheiros=5, vagas=2, area="415", preco=2290000, foto0=76519282, n_fotos=8,
         rua="Avenida do Antão", taxas="",
         descricao="Residência exclusiva no Centro, com vista para o mar.<br/><br/>Terreno com 456m2 e casa com 347m2, "
                   "muito conforto e bom gosto.<br/><br/>São 4 dormitórios, sendo 3 suítes. Suíte principal com "
                   "banheiro com 2 cubas, sala íntima e escritório.<br/><br/>Living amplo, com 4 ambientes.<br/><br/>"
                   "Diferenciais:<br/>Casa recentemente atualizada.<br/>Aquecimento de água a gás.<br/>"
                   "Placas fotovoltaicas.<br/>Aberturas com isolamento acústico.",
         itens=["Área Serviço", "Cozinha Americana", "Lavabo", "Living", "Vista Mar", "Vista Panorâmica"],
         itens_cond=["Banheiro Social"]),
    dict(codigo="45569", id="165140842", tipo="apartamento", bairro_completo="Pântano Do Sul", cidade="Florianópolis",
         quartos=2, suites=1, banheiros=2, vagas=1, area="80", preco=890000, foto0=76554119, n_fotos=6,
         rua="Rua Waldemar de Mello Dias, 1200", taxas="Condomínio: R$ 650,00 | IPTU: R$ 1.800,00/ano",
         descricao="Apartamento a poucos passos da praia do Pântano do Sul.<br/><br/>Sacada com churrasqueira e "
                   "vista para o morro. Condomínio com piscina e salão de festas.",
         itens=["Sacada", "Churrasqueira", "Mobiliado", "Piso porcelanato 80x80"],
         itens_cond=["Piscina", "Salão de Festas", "Elevador"]),
    dict(codigo="45529", id="165140840", tipo="apartamento", bairro_completo="Centro", cidade="Florianópolis",
         quartos=3, suites=1, banheiros=2, vagas=2, area="134", preco=1300000, foto0=76554300, n_fotos=5,
         rua="Avenida Mauro Ramos", taxas="Condomínio: R$ 1.100,00",
         descricao="Apartamento amplo no Centro, perto da Beira-Mar Norte.<br/><br/>Três dormitórios, sendo uma suíte.",
         itens=["Sacada", "Ar Condicionado", "Armários Embutidos"], itens_cond=["Elevador", "Portaria 24h", "Academia"]),
    dict(codigo="33295", id="165131221", tipo="casa", bairro_completo="Jurerê Internacional", cidade="Florianópolis",
         quartos=5, suites=5, banheiros=7, vagas=4, area="825", preco=20800000, foto0=76530000, n_fotos=7,
         rua="Rua dos Fidalgos", taxas="",
         descricao="Casa à beira-mar em Jurerê Internacional, com piscina e acesso direto à praia.",
         itens=["Piscina", "Churrasqueira", "Closet", "Jardim", "Vista Mar"], itens_cond=[]),
    dict(codigo="45601", id="165140901", tipo="estudio", bairro_completo="Saco Grande", cidade="Florianópolis",
         quartos=1, suites=0, banheiros=1, vagas=1, area="33", preco=765000, foto0=76560000, n_fotos=4,
         rua="", taxas="",
         descricao="Studio novo, ideal para investimento em locação.",
         itens=["Mobiliado"], itens_cond=["Coworking", "Academia", "Lavanderia"]),
]


def criar():
    PASTA.mkdir(exist_ok=True)
    for a in AMOSTRAS:
        fotos = [a["foto0"] + i for i in range(a["n_fotos"])]
        galeria = "".join(
            f'<div class="InternaGaleria_Full_Imagem"><img src="https://gralha2.inforcedata.com.br/api/image/{f}.jpg"></div>'
            for f in reversed(fotos))  # fora de ordem de propósito: o extrator reordena
        preco_txt = f"{a['preco']:,}".replace(",", ".")
        nome_tipo = {"casa": "Casa", "apartamento": "Apartamento", "estudio": "Estúdio"}[a["tipo"]]
        h1 = (f"{nome_tipo}\n para\n venda\n com\n {a['quartos']} dormitórios\n em\n "
              f"{a['bairro_completo']}\n com {a['area']} m²")
        endereco = f"<p>Endereço: {a['rua']}</p>" if a["rua"] else ""
        html = MODELO.format(
            resumo=a["descricao"].split("<br/>")[0][:150], foto0=a["foto0"],
            og_titulo=f"{nome_tipo} em {a['bairro_completo']} com {a['quartos']} dormitórios por R$ {preco_txt}",
            tipo=a["tipo"], bairro_completo=a["bairro_completo"], cidade=a["cidade"], quartos=a["quartos"],
            codigo=a["codigo"], galeria=galeria, h1=h1, preco_txt=preco_txt, taxas=a["taxas"], area=a["area"],
            suites=a["suites"], banheiros=a["banheiros"], vagas=a["vagas"], descricao=a["descricao"],
            itens="".join(f'<li><i class="fas fa-check"></i> {i} </li>' for i in a["itens"]),
            itens_cond="".join(f'<li><i class="fas fa-check"></i> {i} </li>' for i in a["itens_cond"]),
            endereco=endereco)
        slug = (f"venda+{a['tipo']}+{a['quartos']}-quartos+{a['bairro_completo'].lower().replace(' ', '-')}"
                f"+{a['cidade'].lower().replace('ó', 'o')}+sc+{a['area']}m2+rs{a['preco']},00")
        (PASTA / f"{a['codigo']}.html").write_text(html, encoding="utf-8")
        (PASTA / f"{a['codigo']}.url").write_text(
            f"https://www.gralhaimoveis.com.br/imovel/{slug}/{a['id']}\n", encoding="utf-8")


if __name__ == "__main__":
    criar()
    print(f"Amostras criadas em {PASTA}")
