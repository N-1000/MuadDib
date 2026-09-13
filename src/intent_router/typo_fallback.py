"""Correccion de typos por distancia de edicion (rapidfuzz), solo como fallback del match exacto."""

from __future__ import annotations

from rapidfuzz import fuzz, process

# Validado contra VERBOS_ACCION: typos de una o dos letras superan 92 de ratio, ruido no relacionado cae por debajo de 45.
UMBRAL_DEFECTO = 90


def corregir_typo(
    token: str,
    vocabulario: frozenset[str],
    *,
    umbral: int = UMBRAL_DEFECTO,
) -> str | None:
    """Devuelve la palabra de `vocabulario` mas parecida a `token` si supera `umbral`, o None."""
    if token in vocabulario:
        return token
    if not vocabulario:
        return None

    resultado = process.extractOne(
        token, vocabulario, scorer=fuzz.ratio, score_cutoff=umbral
    )
    if resultado is None:
        return None

    palabra_corregida, _score, _indice = resultado
    return palabra_corregida
