"""Testes dos critérios de aceite da especificação (rodar: python -m unittest discover tests)."""

import copy
import unittest
from pathlib import Path
from xml.etree import ElementTree

from gerador import fonte, vrsync
from gerador.build import mesclar
from gerador.extrator import extrair

import sys
sys.path.insert(0, str(Path(__file__).parent))
import criar_amostras  # noqa: E402

AMOSTRAS = Path(__file__).parent / "amostras"
CFG = {"nome": "Teste", "email": "a@b.com", "whatsapp": "5548999999999", "site_url": "https://exemplo.com.br",
       "telefone": "48 9999", "exibir_endereco": "Street"}


def carregar(codigo):
    if not (AMOSTRAS / f"{codigo}.html").exists():
        criar_amostras.criar()
    html = (AMOSTRAS / f"{codigo}.html").read_text(encoding="utf-8")
    url = (AMOSTRAS / f"{codigo}.url").read_text(encoding="utf-8").strip()
    return html, url


class TestValidacaoUrl(unittest.TestCase):
    def test_aceita_anuncio_https_da_gralha(self):
        url, erro = fonte.validar_url(
            "https://www.gralhaimoveis.com.br/imovel/venda+casa+4-quartos+centro+florianopolis+sc+346m2+rs2290000,00/165130823")
        self.assertIsNone(erro)

    def test_bloqueia_host_externo_e_sufixo(self):
        for ruim in ("https://evil.com/imovel/venda+casa/1",
                     "https://gralhaimoveis.com.br.evil.com/imovel/venda+casa/1",
                     "https://evilgralhaimoveis.com.br/imovel/venda+casa/1"):
            self.assertIsNotNone(fonte.validar_url(ruim)[1], ruim)

    def test_bloqueia_http_credenciais_e_porta(self):
        for ruim in ("http://www.gralhaimoveis.com.br/imovel/venda+casa/1",
                     "https://user:pw@www.gralhaimoveis.com.br/imovel/venda+casa/1",
                     "https://www.gralhaimoveis.com.br:8443/imovel/venda+casa/1"):
            self.assertIsNotNone(fonte.validar_url(ruim)[1], ruim)

    def test_bloqueia_lancamento_e_locacao(self):
        self.assertIsNotNone(fonte.validar_url("https://www.gralhaimoveis.com.br/lancamento/imovel-novo+x/129")[1])
        self.assertIsNotNone(fonte.validar_url("https://www.gralhaimoveis.com.br/imovel/locacao+casa/1")[1])

    def test_baixar_nao_faz_requisicao_para_host_externo(self):
        r = fonte.baixar("https://evil.com/imovel/venda+casa/1", exigir_anuncio=True)
        self.assertEqual(r.tipo, "bloqueado")


class TestExtrator(unittest.TestCase):
    def test_campos_principais(self):
        p = extrair(*carregar("32819"))["imovel"]
        self.assertEqual(p["codigo"], "32819")  # código oficial, não o id da URL
        self.assertEqual(p["id_tecnico"], "165130823")
        self.assertEqual(p["titulo"], "Casa para venda com 4 dormitórios em Centro Florianópolis com 415 m²")
        self.assertEqual((p["tipo"], p["bairro"], p["cidade"], p["uf"]), ("casa", "Centro", "Florianópolis", "SC"))
        self.assertEqual(p["preco"], 2290000)
        self.assertEqual((p["area"], p["quartos"], p["suites"], p["banheiros"], p["vagas"]), (415, 4, 3, 5, 2))
        self.assertEqual(p["endereco"], "Avenida do Antão")
        self.assertIn("Vista para o mar", p["caracteristicas"])
        self.assertEqual(p["revisar"], [])

    def test_fotos_https_ordenadas_sem_duplicar(self):
        p = extrair(*carregar("32819"))["imovel"]
        self.assertTrue(all(u.startswith("https://") for u in p["fotos"]))
        self.assertEqual(len(p["fotos"]), len(set(p["fotos"])))
        self.assertTrue(p["fotos"][0].endswith("76519282.jpg"))
        ids = [int(u.rsplit("/", 1)[1].split(".")[0]) for u in p["fotos"]]
        self.assertEqual(ids, sorted(ids))

    def test_capa_sem_numero_e_descartada(self):
        html, url = carregar("32819")
        html = html.replace("http://gralha2.inforcedata.com.br/api/image/76519282.jpg",
                            "https://gralha2.inforcedata.com.br/api/image/.jpg")
        p = extrair(html, url)["imovel"]
        self.assertNotIn("https://gralha2.inforcedata.com.br/api/image/.jpg", p["fotos"])
        self.assertTrue(p["fotos"])

    def test_taxas_numero_e_whitelist(self):
        p = extrair(*carregar("45569"))["imovel"]
        self.assertEqual((p["condominio"], p["iptu"], p["periodo_iptu"]), (650, 1800, "Yearly"))
        self.assertEqual((p["endereco"], p["numero"]), ("Rua Waldemar de Mello Dias", "1200"))
        self.assertEqual(p["caracteristicas_removidas"], 1)  # "Piso porcelanato" fora da lista

    def test_pagina_que_nao_e_anuncio(self):
        r = extrair("<html><body>oi</body></html>", "https://www.gralhaimoveis.com.br/imovel/venda+x/1")
        self.assertFalse(r["ok"])


class TestFeed(unittest.TestCase):
    def setUp(self):
        self.imoveis = [extrair(*carregar(c))["imovel"] for c in ("32819", "45569", "45529", "33295", "45601")]

    def test_xml_bem_formado_e_rejeicoes(self):
        xml, rel = vrsync.gerar(CFG, self.imoveis)
        raiz = ElementTree.fromstring(xml.encode("utf-8"))
        ns = {"v": "http://www.vivareal.com/schemas/1.0/VRSync"}
        ids = [e.text for e in raiz.findall(".//v:ListingID", ns)]
        self.assertNotIn("45601", ids)  # sem endereço
        self.assertEqual(rel["sem_endereco"], 1)
        self.assertEqual(rel["exportados"], 4)
        primeira = raiz.find(".//v:Media/v:Item", ns)
        self.assertEqual(primeira.get("primary"), "true")

    def test_sem_preco_sem_foto_e_duplicado(self):
        a, b, c = (copy.deepcopy(self.imoveis[0]) for _ in range(3))
        a["preco"] = None
        a["codigo"] = "X0"
        b["codigo"] = "X1"
        b["fotos"] = ["http://inseguro.jpg"]
        _, rel = vrsync.gerar(CFG, [self.imoveis[0], c, a, b])
        self.assertEqual((rel["exportados"], rel["duplicados"], rel["sem_preco"], rel["sem_foto"]), (1, 1, 1, 1))

    def test_cdata_e_caracteres_invalidos(self):
        p = copy.deepcopy(self.imoveis[0])
        p["descricao"] = "Texto com ]]> e \x01 controle & <tag>"
        xml, _ = vrsync.gerar(CFG, [p])
        ElementTree.fromstring(xml.encode("utf-8"))

    def test_feed_segmentado_respeita_filtros(self):
        feed = {"preco_maximo": 1000000, "bairros": [], "tipos": ["apartamento"]}
        xml, rel = vrsync.gerar(CFG, self.imoveis, feed)
        self.assertEqual(rel["elegiveis"], 1)
        self.assertIn("<ListingID>45569</ListingID>", xml)
        manual = {"selecao": "manual", "incluir_codigos": ["33295"]}
        xml, _ = vrsync.gerar(CFG, self.imoveis, manual)
        self.assertEqual(xml.count("<Listing>"), 1)


class TestAtualizacao(unittest.TestCase):
    def test_reimportar_nao_duplica_e_remocao_em_duas_etapas(self):
        p = extrair(*carregar("32819"))["imovel"]
        url = p["url_origem"]
        imoveis, rel = mesclar(CFG, {"imoveis": []}, [(url, "ok", "", copy.deepcopy(p))], "t1")
        imoveis, rel = mesclar(CFG, {"imoveis": imoveis},
                               [(url, "ok", "", copy.deepcopy(p)), (url, "ok", "", copy.deepcopy(p))], "t2")
        self.assertEqual(len(imoveis), 1)
        self.assertEqual(rel["sem_mudanca"], 2)
        # 1ª vez que some: continua publicado aguardando confirmação
        imoveis, rel = mesclar(CFG, {"imoveis": imoveis}, [(url, "sumiu", "404", None)], "t3")
        self.assertEqual((len(imoveis), rel["aguardando_confirmacao"]), (1, 1))
        # 2ª vez: sai do site e do feed
        imoveis, rel = mesclar(CFG, {"imoveis": imoveis}, [(url, "sumiu", "404", None)], "t4")
        self.assertEqual((len(imoveis), rel["removidos"]), (0, 1))

    def test_erro_temporario_mantem_imovel(self):
        p = extrair(*carregar("32819"))["imovel"]
        imoveis, _ = mesclar(CFG, {"imoveis": []}, [(p["url_origem"], "ok", "", p)], "t1")
        imoveis, rel = mesclar(CFG, {"imoveis": imoveis}, [(p["url_origem"], "erro", "timeout", None)], "t2")
        self.assertEqual((len(imoveis), rel["falhas"]), (1, 1))


class TestDescoberta(unittest.TestCase):
    def test_sitemap_e_listagem(self):
        anuncio = "/imovel/venda+casa+4-quartos+centro+florianopolis+sc+346m2+rs2290000,00/165130823"
        outro = "/imovel/venda+apartamento+2-quartos+centro+florianopolis+sc+68m2+rs890000,00/165140842"
        paginas = {
            "https://www.gralhaimoveis.com.br/sitemap.xml":
                '<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><sitemap>'
                '<loc>https://www.gralhaimoveis.com.br/sitemap-1.xml</loc></sitemap></sitemapindex>',
            "https://www.gralhaimoveis.com.br/sitemap-1.xml":
                f'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><url><loc>https://www.gralhaimoveis.com.br{anuncio}</loc></url>'
                '<url><loc>https://www.gralhaimoveis.com.br/lancamento/imovel-novo+x/129</loc></url></urlset>',
            "https://www.gralhaimoveis.com.br/": '<a href="/venda?pagina=2">2</a><a href="https://evil.com/venda">x</a>',
            "https://www.gralhaimoveis.com.br/venda": "",
            "https://www.gralhaimoveis.com.br/venda?pagina=2": f'<a href="{outro}">ap</a><a href="{anuncio}">casa</a>',
        }
        visitados = []

        def falso(url, tipos_aceitos=("text/html",), exigir_anuncio=False):
            visitados.append(url)
            if url in paginas:
                return fonte.Resposta("ok", texto=paginas[url], url=url)
            return fonte.Resposta("sumiu", mensagem="404")

        urls, resumo = fonte.descobrir(baixar_fn=falso, pausa=0, log=lambda *_: None)
        self.assertEqual(len(urls), 2)
        self.assertEqual((resumo["sitemap"], resumo["listagens"]), (1, 1))
        self.assertFalse(any("evil.com" in u for u in visitados))


if __name__ == "__main__":
    unittest.main()
