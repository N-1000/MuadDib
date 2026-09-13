"""Marca conector/negacion en un mensaje normalizado, sin interpretar el mensaje."""

from __future__ import annotations

import re
from dataclasses import dataclass

from intent_router.lexicon import CONECTORES, NEGACIONES

_PATRON_TOKEN = re.compile(r"\w+", re.UNICODE)


@dataclass(frozen=True)
class SenalTripwire:
    """Resultado auditable: que palabras de CONECTORES/NEGACIONES aparecieron."""

    conectores: frozenset[str]
    negaciones: frozenset[str]

    @property
    def tiene_conector(self) -> bool:
        return bool(self.conectores)

    @property
    def tiene_negacion(self) -> bool:
        return bool(self.negaciones)


def detectar_senales(texto_normalizado: str) -> SenalTripwire:
    """Cruza los tokens de `texto_normalizado` contra CONECTORES y NEGACIONES."""
    tokens = frozenset(_PATRON_TOKEN.findall(texto_normalizado))
    return SenalTripwire(
        conectores=tokens & CONECTORES,
        negaciones=tokens & NEGACIONES,
    )
