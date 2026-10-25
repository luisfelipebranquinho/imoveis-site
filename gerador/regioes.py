"""Agrupa os bairros da Grande Florianópolis em regiões, para a busca por região."""

from .textos import chave

REGIOES_FLORIPA = {
    "Norte da Ilha": [
        "Jurerê", "Jurerê Internacional", "Jurerê Tradicional", "Canasvieiras", "Ingleses", "Ingleses do Rio Vermelho",
        "Ingleses Norte", "Ingleses Sul", "Santinho", "Cachoeira do Bom Jesus", "Ponta das Canas", "Lagoinha",
        "Praia Brava", "Daniela", "Forte", "Santo Antônio de Lisboa", "Sambaqui", "Cacupé", "Ratones",
        "Vargem Grande", "Vargem Pequena", "Vargem do Bom Jesus", "Canto do Lamim", "Barra do Sambaqui",
    ],
    "Leste da Ilha": [
        "Lagoa da Conceição", "Barra da Lagoa", "Joaquina", "Canto da Lagoa", "Porto da Lagoa", "Rio Vermelho",
        "Praia Mole", "Retiro da Lagoa", "Costa da Lagoa", "São João do Rio Vermelho", "Moçambique",
    ],
    "Sul da Ilha": [
        "Campeche", "Novo Campeche", "Areias do Campeche", "Rio Tavares", "Morro das Pedras", "Armação",
        "Armação do Pântano do Sul", "Pântano do Sul", "Ribeirão da Ilha", "Tapera", "Carianos",
        "Costeira do Pirajubaé", "Açores", "Lagoa Pequena", "Alto Ribeirão", "Caieira da Barra do Sul",
        "Solidão", "Matadeiro", "Ressacada", "Base Aérea",
    ],
    "Região Central": [
        "Centro", "Agronômica", "Trindade", "Córrego Grande", "Santa Mônica", "Itacorubi", "João Paulo",
        "Saco Grande", "Monte Verde", "Pantanal", "Carvoeira", "José Mendes", "Saco dos Limões", "Serrinha",
        "Prainha", "Morro da Cruz", "Parque São Jorge", "Jardim Anchieta", "Costeira", "Mont Serrat",
    ],
    "Região Continental": [
        "Estreito", "Coqueiros", "Capoeiras", "Abraão", "Balneário", "Itaguaçu", "Bom Abrigo", "Jardim Atlântico",
        "Canto", "Monte Cristo", "Coloninha", "Sapé", "Vila São João", "Jardim Continental",
    ],
}

_INDICE = {chave(b): r for r, bairros in REGIOES_FLORIPA.items() for b in bairros}

ORDEM = ["Norte da Ilha", "Leste da Ilha", "Sul da Ilha", "Região Central", "Região Continental",
         "São José", "Palhoça", "Biguaçu"]


def regiao(bairro: str, cidade: str) -> str:
    c = chave(cidade)
    if c == "florianopolis":
        b = chave(bairro)
        if b in _INDICE:
            return _INDICE[b]
        # nomes compostos, ex.: "Centro Florianópolis", "Canasvieiras Norte"
        for nome, r in _INDICE.items():
            if b.startswith(nome + " ") or b.endswith(" " + nome):
                return r
        return "Outros bairros de Florianópolis"
    return cidade or "Outras cidades"
