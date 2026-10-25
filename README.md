# Site de imóveis

Site estático que mostra os imóveis à venda da Gralha Imóveis, com botões de WhatsApp e e-mail em cada anúncio, e gera o feed VRSync para os portais (Viva Real/ZAP).

Tudo roda de graça no GitHub: todo dia às 06:17 o GitHub Actions lê os anúncios na Gralha, monta as páginas e publica no GitHub Pages. Não há banco de dados nem servidor.

## Endereços

- Site: `https://luisfelipebranquinho.github.io/imoveis-site/`
- Feed geral para portais: `https://luisfelipebranquinho.github.io/imoveis-site/vrsync.xml`
- Feeds segmentados: `.../vrsync/{slug}.xml` (configurados em `feeds.json`)
- Relatório da última atualização: `.../dados/relatorio.json`

## Como ajustar (pelo próprio site do GitHub)

Abra o arquivo, clique no lápis (Edit), altere e clique em **Commit changes**. O site é refeito em poucos minutos.

| Arquivo | Para quê |
|---|---|
| `config.json` | Nome, WhatsApp (com 55 + DDD), e-mail, telefone, horário, CRECI, Instagram/Facebook, frases da página inicial, mensagem do WhatsApp |
| `config.json` → `imagem_capa` | Link de uma foto para o topo da página (vazio = foto de um imóvel em destaque) |
| `config.json` → `alto_padrao_a_partir` | Valor mínimo para entrar no carrossel "Alto padrão" |
| `config.json` → `destaques` | Códigos dos imóveis que aparecem primeiro, ex.: `["32819", "45569"]` |
| `config.json` → `ocultar` | Códigos que não devem aparecer no site nem no feed |
| `config.json` → `lancamentos` | Códigos marcados como lançamento |
| `feeds.json` | Feeds segmentados (faixa de preço, bairros, tipos, seleção manual). `"ativo": false` pausa o feed (o endereço passa a dar 404) |
| `imoveis-extras.txt` | Links de anúncios que devem entrar mesmo se a busca automática não encontrar |

## Atualizar agora

Aba **Actions** → **Atualizar site** → **Run workflow**. O resumo da execução mostra quantos imóveis foram lidos, atualizados, removidos e rejeitados no feed.

## Regras importantes

- Só entram anúncios de **venda** individuais (`/imovel/venda+.../número`). Páginas de lançamento com faixa de preço ficam de fora.
- Um imóvel que some da Gralha só sai do site na **segunda** verificação seguida (confirmação). Falhas temporárias de rede não removem nada.
- Se o número de imóveis cair pela metade de uma vez, a publicação é cancelada para não apagar o site por engano. Para publicar mesmo assim, rode manualmente marcando "forçar".
- O feed rejeita anúncios sem preço, sem foto HTTPS, sem endereço, sem área ou com tipo sem correspondência (ver relatório).
- Divulgue apenas imóveis que você está autorizada a anunciar. A aceitação do feed depende da homologação com cada portal.

## Para desenvolvedores

```bash
pip install -r requirements.txt
python -m unittest discover tests        # testes
python tests/criar_amostras.py           # páginas de exemplo no formato da Gralha
python -m gerador.build --amostra tests/amostras   # gera ./publicar sem internet
python -m http.server -d publicar        # ver em http://localhost:8000
```

Código: `gerador/fonte.py` (validação de URL e download seguro), `gerador/extrator.py` (leitura do anúncio), `gerador/vrsync.py` (XML), `gerador/site.py` (HTML), `gerador/build.py` (junta tudo). Visual em `site/assets/`.
