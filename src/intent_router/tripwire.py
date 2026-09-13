"""Señales estructurales baratas para el nivel 0 (reglas) del router.

Marca si un mensaje ya normalizado contiene un conector (posible
multi-intencion) o una negacion (posible exclusion). No interpreta el
mensaje ni decide nada: eso lo hace quien orquesta la cascada
(`router.py`), que decide cuando NO confiar en un solo match de reglas.

NOTA: nombre de archivo provisional, no esta fijado en la tabla de
modulos del CLAUDE.md.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from intent_router.lexicon import CONECTORES, NEGACIONES

_PATRON_TOKEN = re.compile(r"\w+", re.UNICODE)


@dataclass(frozen=True)
class SenalTripwire:
    """Resultado auditable de inspeccionar un mensaje: que palabras de
    cada lista aparecieron, no solo si aparecieron."""

    conectores: frozenset[str]
    negaciones: frozenset[str]

    @property
    def tiene_conector(self) -> bool:
        return bool(self.conectores)

    @property
    def tiene_negacion(self) -> bool:
        return bool(self.negaciones)


def detectar_senales(texto_normalizado: str) -> SenalTripwire:
    """Compara los tokens de `texto_normalizado` (ya pasado por
    `normalizer.normalize`) contra CONECTORES y NEGACIONES.

    Tokeniza por palabra completa (`\\w+`) para no confundir substrings
    (p. ej. "notificar" no debe activar la negacion "no").
    """
    tokens = frozenset(_PATRON_TOKEN.findall(texto_normalizado))
    return SenalTripwire(
        conectores=tokens & CONECTORES,
        negaciones=tokens & NEGACIONES,
    )
