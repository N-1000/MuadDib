"""Normalizacion de texto de entrada para el router: minusculas, sin diacriticos salvo la ñ."""

import unicodedata

_ENIE_PLACEHOLDER = chr(0xE000)

assert _ENIE_PLACEHOLDER != ""
assert unicodedata.category(_ENIE_PLACEHOLDER) == "Co"

_CONTROL_CATEGORIES = {"Cc", "Cf"}


def normalize(texto: str, *, longitud_maxima: int = 2000) -> str:
    """Normaliza texto de usuario: minusculas, sin diacriticos salvo la ñ, sin caracteres de control, truncado a longitud_maxima."""
    if not isinstance(texto, str):
        raise TypeError("texto debe ser str")
    if longitud_maxima <= 0:
        raise ValueError("longitud_maxima debe ser positiva")

    texto = unicodedata.normalize("NFC", texto)
    texto = texto[:longitud_maxima]
    texto = texto.lower()

    texto = texto.replace(_ENIE_PLACEHOLDER, "")
    texto = texto.replace("ñ", _ENIE_PLACEHOLDER)

    descompuesto = unicodedata.normalize("NFD", texto)
    sin_diacriticos = "".join(
        caracter
        for caracter in descompuesto
        if unicodedata.category(caracter) != "Mn"
    )
    recompuesto = unicodedata.normalize("NFC", sin_diacriticos)

    recompuesto = recompuesto.replace(_ENIE_PLACEHOLDER, "ñ")

    sin_control = "".join(
        caracter
        for caracter in recompuesto
        if unicodedata.category(caracter) not in _CONTROL_CATEGORIES
    )

    return sin_control
