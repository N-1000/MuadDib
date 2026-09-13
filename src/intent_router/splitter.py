"""Divide un mensaje normalizado en clausulas separadas por conectores, sin decidir cual es la principal."""

from __future__ import annotations

import re

from intent_router.lexicon import CONECTORES

_PATRON_CONECTORES = re.compile(
    r"\b(?:"
    + "|".join(re.escape(c) for c in sorted(CONECTORES, key=len, reverse=True))
    + r")\b",
    re.UNICODE,
)


def dividir_por_conectores(texto_normalizado: str) -> list[str]:
    """Separa `texto_normalizado` en clausulas por CONECTORES, descartando pedazos vacios."""
    pedazos = _PATRON_CONECTORES.split(texto_normalizado)
    return [pedazo.strip() for pedazo in pedazos if pedazo.strip()]
