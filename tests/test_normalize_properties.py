import inspect
import unicodedata

from hypothesis import given, settings, strategies as st

from intent_router.normalizer import normalize

_ALFABETO = st.sampled_from(
    list("abcdefghijklmnopqrstuvwxyzñÑ0123456789 \t\n.,;:¿?¡!")
    + ["á", "é", "í", "ó", "ú", "Á", "É", "Í", "Ó", "Ú", "ü", "Ü"]
    + ["\u0301", "\u0303", "\u0308"]
    + ["\x00", "\x1f", "\ufeff"]
    + ["\U0001F600", "\U0001F440", "\U0001F4CA", "\u26a0", "\ufe0f"]
)

_MAX_SIZE_TEXTOS = 200
_TEXTOS = st.text(alphabet=_ALFABETO, max_size=_MAX_SIZE_TEXTOS)

_LONGITUD_MAXIMA_DEFECTO = inspect.signature(normalize).parameters["longitud_maxima"].default

assert _MAX_SIZE_TEXTOS < _LONGITUD_MAXIMA_DEFECTO, "_TEXTOS no debe poder truncarse: rompe el supuesto de la propiedad 3"


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
