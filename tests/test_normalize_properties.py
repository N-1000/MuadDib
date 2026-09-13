import unicodedata

from hypothesis import given, settings, strategies as st

from intent_router.normalizer import normalize

_ALFABETO = st.sampled_from(
    list("abcdefghijklmnopqrstuvwxyzñÑ0123456789 \t\n.,;:¿?¡!")
    + ["á", "é", "í", "ó", "ú", "Á", "É", "Í", "Ó", "Ú", "ü", "Ü"]
    + ["́", "̃", "̈"]
    + ["\x00", "\x1f", "﻿"]
)

_TEXTOS = st.text(alphabet=_ALFABETO, max_size=200)


@settings(max_examples=1000)
@given(texto=_TEXTOS)
def test_normalize_es_idempotente(texto):
    salida = normalize(texto)
    assert normalize(salida) == salida


@settings(max_examples=1000)
@given(texto=_TEXTOS, longitud_maxima=st.integers(min_value=1, max_value=500))
def test_normalize_respeta_cota_de_longitud(texto, longitud_maxima):
    salida = normalize(texto, longitud_maxima=longitud_maxima)
    assert len(salida) <= longitud_maxima


@settings(max_examples=1000)
@given(texto=_TEXTOS)
def test_normalize_sin_mn_residual_y_ene_sobrevive(texto):
    salida = normalize(texto)
    assert all(unicodedata.category(c) != "Mn" for c in salida)
    texto_nfc = unicodedata.normalize("NFC", texto)
    if "ñ" in texto_nfc.lower():
        assert "ñ" in salida
