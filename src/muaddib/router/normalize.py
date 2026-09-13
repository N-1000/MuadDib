"""Normalizacion de texto de entrada para el router.

Quita diacriticos (acentos) preservando la ene con tilde, porque en
espanol "ano" y "año" son palabras distintas. No hace tokenizacion,
stemming ni parsing sintactico: eso es responsabilidad de otras capas.
"""

import unicodedata

_ENIE_PLACEHOLDER = ""

_CONTROL_CATEGORIES = {"Cc", "Cf"}


def normalize_text(texto: str, *, longitud_maxima: int = 2000) -> str:
    """Normaliza texto de usuario: minusculas, sin diacriticos (menos la ñ),
    sin caracteres de control, truncado a longitud_maxima.

    Es una funcion pura: misma entrada, misma salida, sin efectos secundarios.
    """
    if not isinstance(texto, str):
        raise TypeError("texto debe ser str")
    if longitud_maxima <= 0:
        raise ValueError("longitud_maxima debe ser positiva")

    texto = texto[:longitud_maxima]
    texto = texto.lower()

    # Si el texto trae el caracter usado como marcador interno (raro, pero
    # posible como intento de manipular la normalizacion), se descarta antes
    # de usarlo como sentinel para no confundirlo con una ñ real.
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
