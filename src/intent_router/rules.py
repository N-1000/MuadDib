"""Orquesta los primitivos de nivel 0 sobre un mensaje crudo, sin conocer `config` todavia."""

from __future__ import annotations

import re
from dataclasses import dataclass

from intent_router.lexicon import VERBOS_ACCION
from intent_router.normalizer import normalize
from intent_router.splitter import dividir_por_conectores
from intent_router.tripwire import SenalTripwire, detectar_senales
from intent_router.typo_fallback import corregir_typo
from intent_router.verb_variants import resolver_verbo

_PATRON_TOKEN = re.compile(r"\w+", re.UNICODE)


@dataclass(frozen=True)
class ClausulaAnalizada:
    """Una clausula del mensaje junto con el infinitivo de accion que se le pudo asociar, si hay uno."""

    texto: str
    verbo: str | None


@dataclass(frozen=True)
class AnalisisNivel0:
    """Resultado auditable de nivel 0: texto normalizado, senales del tripwire y clausulas ya resueltas."""

    texto_normalizado: str
    senales: SenalTripwire
    clausulas: tuple[ClausulaAnalizada, ...]


def _resolver_verbo_de_clausula(clausula: str) -> str | None:
    for token in _PATRON_TOKEN.findall(clausula):
        verbo = resolver_verbo(token) or corregir_typo(token, VERBOS_ACCION)
        if verbo is not None:
            return verbo
    return None


def analizar(mensaje: str) -> AnalisisNivel0:
    """Normaliza `mensaje`, detecta señales y resuelve un verbo de accion por clausula."""
    texto_normalizado = normalize(mensaje)
    senales = detectar_senales(texto_normalizado)

    textos_clausulas = (
        dividir_por_conectores(texto_normalizado)
        if senales.tiene_conector
        else [texto_normalizado]
    )

    clausulas = tuple(
        ClausulaAnalizada(texto=texto, verbo=_resolver_verbo_de_clausula(texto))
        for texto in textos_clausulas
    )

    return AnalisisNivel0(
        texto_normalizado=texto_normalizado,
        senales=senales,
        clausulas=clausulas,
    )
