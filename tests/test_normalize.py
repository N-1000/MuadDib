import pytest

from muaddib.router.normalize import normalize_text


def test_preserva_ene_con_tilde():
    assert normalize_text("año") == "año"
    assert normalize_text("año") != "ano"


def test_ene_con_tilde_mayuscula():
    assert normalize_text("AÑO") == "año"
    assert normalize_text("Ñoño") == "ñoño"


def test_quita_acentos_normales():
    assert normalize_text("café") == "cafe"
    assert normalize_text("acción") == "accion"
    assert normalize_text("múltiple") == "multiple"


def test_pasa_a_minusculas():
    assert normalize_text("HOLA Mundo") == "hola mundo"


def test_quita_caracteres_de_control():
    assert normalize_text("hola\x00mundo") == "holamundo"
    assert normalize_text("hola\tmundo") == "holamundo"
    assert normalize_text("hola\nmundo") == "holamundo"


def test_no_toca_puntuacion_ni_numeros():
    assert normalize_text("¿Cuánto contamina PM2.5 hoy?") == "¿cuanto contamina pm2.5 hoy?"


def test_string_vacio():
    assert normalize_text("") == ""


def test_trunca_a_longitud_maxima():
    texto = "a" * 100
    assert normalize_text(texto, longitud_maxima=10) == "a" * 10


def test_intento_de_inyectar_marcador_interno():
    caracter_marcador_interno = ""
    resultado = normalize_text(f"hola{caracter_marcador_interno}mundo")
    assert "ñ" not in resultado
    assert resultado == "holamundo"


def test_rechaza_tipo_no_str():
    with pytest.raises(TypeError):
        normalize_text(123)  # type: ignore[arg-type]


def test_rechaza_longitud_maxima_no_positiva():
    with pytest.raises(ValueError):
        normalize_text("hola", longitud_maxima=0)


def test_es_funcion_pura_idempotente_en_su_propia_salida():
    texto = "El Año de la Contaminación en Cali"
    resultado = normalize_text(texto)
    assert normalize_text(resultado) == resultado
