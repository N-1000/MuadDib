"""Divide un mensaje normalizado en clausulas separadas por conectores.

Split literal, no interpretacion: no decide cual clausula es la intencion
"principal", solo separa el texto en pedazos mas chicos para que el nivel
de reglas intente matchear cada uno por separado. Pensado para cuando el
tripwire (`tripwire.py`) marco `tiene_conector`.

NOTA: nombre de archivo provisional, no esta fijado en la tabla de
modulos del CLAUDE.md.
"""

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
    """Separa `texto_normalizado` en las clausulas delimitadas por
    cualquier palabra completa de CONECTORES. Descarta pedazos vacios o
    que quedan en blanco tras el split (conectores pegados, al borde,
    o repetidos).
    """
    pedazos = _PATRON_CONECTORES.split(texto_normalizado)
    return [pedazo.strip() for pedazo in pedazos if pedazo.strip()]
