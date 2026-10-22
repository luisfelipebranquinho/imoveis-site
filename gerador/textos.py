"""Funções pequenas de texto e números usadas em todo o gerador."""

import re
import unicodedata

_XML_INVALIDO = re.compile("[\u0000-\u0008\u000b\u000c\u000e-\u001f￾￿]")


def limpar(texto: str | None) -> str:
    """Remove caracteres inválidos em XML e colapsa espaços numa linha só."""
    if not texto:
        return ""
    texto = _XML_INVALIDO.sub("", texto)
    return re.sub(r"[ \t\r\n ]+", " ", texto).strip()


def sem_acento(texto: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFD", texto) if unicodedata.category(c) != "Mn"
    )


def chave(texto: str) -> str:
    """Versão sem acento, minúscula e com espaços simples (para comparar rótulos)."""
    return re.sub(r"\s+", " ", sem_acento(limpar(texto)).lower()).strip()


def slug(texto: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", chave(texto)).strip("-")


def numero_br(texto: str) -> float | None:
    """Converte "2.290.000", "82,10", "415m²" em número."""
    m = re.search(r"\d[\d.]*(?:,\d+)?", texto or "")
    if not m:
        return None
    bruto = m.group(0).rstrip(".")
    if "," in bruto:
        bruto = bruto.replace(".", "").replace(",", ".")
    elif re.fullmatch(r"\d{1,3}(\.\d{3})+", bruto):
        bruto = bruto.replace(".", "")
    try:
        return float(bruto)
    except ValueError:
        return None


def dinheiro(texto: str) -> float | None:
    m = re.search(r"R\$\s*(\d[\d.]*(?:,\d{1,2})?)", texto or "", re.I)
    return numero_br(m.group(1)) if m else None


def inteiro_ou_decimal(n: float) -> int | float:
    return int(n) if float(n).is_integer() else round(n, 2)


def brl(valor: float | None) -> str:
    if valor is None:
        return "Valor sob consulta"
    inteiro = f"{int(round(valor)):,}".replace(",", ".")
    return f"R$ {inteiro}"
