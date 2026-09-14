import re

from intent_router.normalizer import normalize

# Documenta, no arregla: el patron \w+ que usan tripwire.py y rules.py
# no incluye "." ni ",", asi que un token alfanumerico con puntuacion
# interna se parte en dos. normalize() deja la puntuacion intacta a
# proposito; el corte pasa en el tokenizador de un nivel mas arriba.
# Sirve de referencia para cuando entities.py tenga que reconocer estos
# tokens completos contra la config de un cliente.
_PATRON_TOKEN = re.compile(r"\w+", re.UNICODE)


def _tokenizar(texto: str) -> list[str]:
    return _PATRON_TOKEN.findall(normalize(texto))


def test_punto_decimal_parte_el_token():
    assert _tokenizar("el sensor marca 12.5 grados") == [
        "el", "sensor", "marca", "12", "5", "grados",
    ]


def test_coma_decimal_parte_el_token():
    assert _tokenizar("la medicion es 8,3 microgramos") == [
        "la", "medicion", "es", "8", "3", "microgramos",
    ]


def test_codigo_alfanumerico_con_punto_se_parte():
    assert _tokenizar("PM2.5 esta alto hoy") == [
        "pm2", "5", "esta", "alto", "hoy",
    ]


def test_codigo_alfanumerico_sin_puntuacion_no_se_parte():
    assert _tokenizar("revisa el co2 del sensor") == [
        "revisa", "el", "co2", "del", "sensor",
    ]


def test_zwj_se_pierde_y_rompe_el_emoji_compuesto():
    # normalize() saca U+200D (ZERO WIDTH JOINER) porque es categoria Cf,
    # la misma que se usa para sacar caracteres de control. El emoji de
    # familia (persona+ZWJ+persona+ZWJ+persona) entra como 5 codepoints
    # y sale como 3 emojis sueltos, sin el joiner que los componia.
    familia = "\U0001F468\u200d\U0001F469\u200d\U0001F467"
    assert len(familia) == 5
    resultado = normalize(familia)
    assert resultado == "\U0001F468\U0001F469\U0001F467"
    assert len(resultado) == 3
