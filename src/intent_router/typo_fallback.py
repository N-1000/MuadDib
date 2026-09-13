"""Correccion de typos como fallback, solo cuando el match exacto fallo.

Usa rapidfuzz (MIT, permite producto cerrado) por distancia de edicion.
Umbral alto a proposito: preferimos no corregir un token ambiguo a
corregirlo mal y matchear una intencion equivocada. Validado contra
casos reales de typos en `VERBOS_ACCION` (ver tests): errores de una o
dos letras superan 92 de ratio; ruido no relacionado cae por debajo de 45.

NOTA: nombre de archivo provisional, no esta fijado en la tabla de
modulos del CLAUDE.md.
"""

from __future__ import annotations

from rapidfuzz import fuzz, process

UMBRAL_DEFECTO = 90


def corregir_typo(
    token: str,
    vocabulario: frozenset[str],
    *,
    umbral: int = UMBRAL_DEFECTO,
) -> str | None:
    """Busca en `vocabulario` la palabra mas parecida a `token`.

    Devuelve la palabra corregida solo si supera `umbral` (0-100, ratio
    de rapidfuzz); si no hay ninguna por encima del umbral, devuelve
    None en vez de adivinar. Se llama por token individual, unicamente
    cuando ya se sabe que `token` no matcheo por pertenencia exacta al
    set correspondiente.
    """
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
