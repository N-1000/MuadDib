"""Orquesta los primitivos de nivel 0 sobre un mensaje crudo, sin conocer `config` todavia."""

from __future__ import annotations

import re
from dataclasses import dataclass

from intent_router.lexicon import DETERMINANTES, VERBOS_ACCION
from intent_router.normalizer import normalize
from intent_router.splitter import dividir_por_conectores
from intent_router.tripwire import SenalTripwire, detectar_senales
from intent_router.typo_fallback import corregir_typo
from intent_router.verb_variants import resolver_verbo

_PATRON_TOKEN = re.compile(r"\w+", re.UNICODE)

_MINIMO_VERBOS_PARA_MULTI_INTENCION = 2


@dataclass(frozen=True)
class ClausulaAnalizada:
    """Una clausula con su verbo de accion (si hay) y sus propias negaciones, para que la exclusion no dependa de una senal global."""

    texto: str
    verbo: str | None
    negaciones: frozenset[str]

    @property
    def negada(self) -> bool:
        return bool(self.negaciones)


@dataclass(frozen=True)
class AnalisisNivel0:
    """Resultado auditable de nivel 0: texto normalizado, senales del mensaje completo y clausulas ya resueltas."""

    texto_normalizado: str
    senales: SenalTripwire
    clausulas: tuple[ClausulaAnalizada, ...]


def _resolver_verbo_de_clausula(clausula: str) -> str | None:
    anterior: str | None = None
    for token in _PATRON_TOKEN.findall(clausula):
        if anterior in DETERMINANTES:
            anterior = token
            continue
        verbo = resolver_verbo(token) or corregir_typo(token, VERBOS_ACCION)
        if verbo is not None:
            return verbo
        anterior = token
    return None


def _analizar_clausula(texto: str) -> ClausulaAnalizada:
    return ClausulaAnalizada(
        texto=texto,
        verbo=_resolver_verbo_de_clausula(texto),
        negaciones=detectar_senales(texto).negaciones,
    )


def analizar(mensaje: str) -> AnalisisNivel0:
    """Normaliza `mensaje`, detecta senales y resuelve verbo y negacion por clausula."""
    texto_normalizado = normalize(mensaje)
    senales = detectar_senales(texto_normalizado)

    clausula_unica = (_analizar_clausula(texto_normalizado),)

    if not senales.tiene_conector:
        return AnalisisNivel0(texto_normalizado, senales, clausula_unica)

    candidatas = tuple(
        _analizar_clausula(texto)
        for texto in dividir_por_conectores(texto_normalizado)
    )
    con_verbo = sum(1 for c in candidatas if c.verbo is not None)

    clausulas = (
        candidatas
        if con_verbo >= _MINIMO_VERBOS_PARA_MULTI_INTENCION
        else clausula_unica
    )

    return AnalisisNivel0(texto_normalizado, senales, clausulas)
