import pytest

from intent_router.normalizer import normalize


def test_preserva_ene_con_tilde():
    assert normalize("año") == "año"
    assert normalize("año") != "ano"


def test_ene_con_tilde_mayuscula():
    assert normalize("AÑO") == "año"
    assert normalize("Ñoño") == "ñoño"


def test_quita_acentos_normales():
    assert normalize("café") == "cafe"
    assert normalize("acción") == "accion"
    assert normalize("múltiple") == "multiple"


def test_pasa_a_minusculas():
    assert normalize("HOLA Mundo") == "hola mundo"


def test_quita_caracteres_de_control():
    assert normalize("hola\x00mundo") == "holamundo"
    assert normalize("hola\tmundo") == "holamundo"
    assert normalize("hola\nmundo") == "holamundo"


def test_no_toca_puntuacion_ni_numeros():
    assert normalize("¿Cuánto contamina PM2.5 hoy?") == "¿cuanto contamina pm2.5 hoy?"


def test_string_vacio():
    assert normalize("") == ""


def test_trunca_a_longitud_maxima():
    texto = "a" * 100
    assert normalize(texto, longitud_maxima=10) == "a" * 10


def test_intento_de_inyectar_marcador_interno():
    caracter_marcador_interno = ""
    resultado = normalize(f"hola{caracter_marcador_interno}mundo")
    assert "ñ" not in resultado
    assert resultado == "holamundo"


def test_rechaza_tipo_no_str():
    with pytest.raises(TypeError):
        normalize(123)  # type: ignore[arg-type]


def test_rechaza_longitud_maxima_no_positiva():
    with pytest.raises(ValueError):
        normalize("hola", longitud_maxima=0)


def test_es_funcion_pura_idempotente_en_su_propia_salida():
    texto = "El Año de la Contaminación en Cali"
    resultado = normalize(texto)
    assert normalize(resultado) == resultado
