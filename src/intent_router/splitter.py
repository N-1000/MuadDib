"""Divide un mensaje normalizado en clausulas separadas por conectores coordinantes, sin decidir cual es la principal."""

from __future__ import annotations

import re

from intent_router.lexicon import CONECTORES_COORDINANTES

_PATRON_CONECTORES = re.compile(
    r"\b(?:"
    + "|".join(re.escape(c) for c in sorted(CONECTORES_COORDINANTES, key=len, reverse=True))
    + r")\b",
    re.UNICODE,
)


def dividir_por_conectores(texto_normalizado: str) -> list[str]:
    """Separa `texto_normalizado` en clausulas por CONECTORES_COORDINANTES, descartando pedazos vacios."""
    pedazos = _PATRON_CONECTORES.split(texto_normalizado)
    return [pedazo.strip() for pedazo in pedazos if pedazo.strip()]
