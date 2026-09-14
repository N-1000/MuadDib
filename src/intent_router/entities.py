"""Deteccion de entidades por keyword contra el entity_catalog de config."""

from typing import Any

from intent_router.normalizer import normalize


def extract_entities(texto: str, config: dict[str, Any]) -> dict[str, list[str]]:
    """Detecta, por tipo, los valores de entity_catalog cuya keyword aparece en texto."""
    texto_norm = normalize(texto)
    catalogo = config.get("entity_catalog", {})

    resultado: dict[str, list[str]] = {}
    for tipo, entradas in catalogo.items():
        valores = _valores_detectados(texto_norm, entradas)
        if valores:
            resultado[tipo] = valores
    return resultado


def _valores_detectados(texto_norm: str, entradas: list[dict[str, Any]]) -> list[str]:
    """Devuelve, en orden, los 'value' cuya keyword aparece en texto_norm."""
    valores: list[str] = []
    for entrada in entradas:
        keywords = [normalize(k) for k in entrada.get("keywords", [])]
        if any(k in texto_norm for k in keywords):
            valores.append(entrada["value"])
    return valores
