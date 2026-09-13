"""Correccion de typos por distancia de edicion (rapidfuzz), solo como fallback del match exacto."""

from __future__ import annotations

from rapidfuzz import fuzz, process

# Validado contra VERBOS_ACCION: typos de una o dos letras superan 92 de ratio, ruido no relacionado cae por debajo de 45.
UMBRAL_DEFECTO = 90

# Validado contra el caso real "confirurar" (configurar=90.0, confirmar=84.2, gap=5.8): un margen de 10 lo marca ambiguo.
MARGEN_AMBIGUEDAD_DEFECTO = 10


def corregir_typo(
    token: str,
    vocabulario: frozenset[str],
    *,
    umbral: int = UMBRAL_DEFECTO,
    margen_ambiguedad: int = MARGEN_AMBIGUEDAD_DEFECTO,
) -> str | None:
    """Devuelve la palabra de `vocabulario` mas parecida a `token` si supera `umbral` y no esta a menos de `margen_ambiguedad` de la segunda mejor, o None."""
    if token in vocabulario:
        return token
    if not vocabulario:
        return None

    candidatos = process.extract(token, vocabulario, scorer=fuzz.ratio, limit=2)
    if not candidatos:
        return None

    mejor_palabra, mejor_score, _indice = candidatos[0]
    if mejor_score < umbral:
        return None

    if len(candidatos) > 1:
        _segunda_palabra, segundo_score, _indice2 = candidatos[1]
        if mejor_score - segundo_score < margen_ambiguedad:
            return None

    return mejor_palabra
