import pytest

from intent_router.normalizer import normalize


def test_caso_1_preserva_ene_con_tilde():
    assert normalize("año") == "año"


def test_caso_2_mayuscula_con_ene_a_minuscula():
    assert normalize("AÑO") == "año"


def test_caso_3_ene_sin_tilde_no_se_toca():
    assert normalize("ano") == "ano"


def test_caso_4_quita_acento_normal():
    assert normalize("camión") == "camion"


def test_caso_5_string_vacio():
    assert normalize("") == ""


def test_caso_6_trunca_a_longitud_maxima_por_defecto():
    assert len(normalize("a" * 5000)) == 2000


def test_caso_7_quita_caracter_de_control():
    assert normalize("hola\x00mundo") == "holamundo"


def test_caso_8_tipo_no_str_lanza_typeerror():
    with pytest.raises(TypeError):
        normalize(123)


def test_caso_9_longitud_maxima_no_positiva_lanza_valueerror():
    with pytest.raises(ValueError):
        normalize("hola", longitud_maxima=0)


def test_caso_10_ene_en_forma_nfd_sobrevive():
    assert normalize("N" + "\u0303") == "ñ"
