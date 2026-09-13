from intent_router.normalizer import _ENIE_PLACEHOLDER, normalize


def test_preserva_ene_con_tilde():
    assert normalize("año") != "ano"


def test_ene_con_tilde_mayuscula():
    assert normalize("Ñoño") == "ñoño"


def test_quita_acentos_normales():
    assert normalize("café") == "cafe"
    assert normalize("acción") == "accion"
    assert normalize("múltiple") == "multiple"


def test_pasa_a_minusculas():
    assert normalize("HOLA Mundo") == "hola mundo"


def test_quita_caracteres_de_control():
    assert normalize("hola\tmundo") == "holamundo"
    assert normalize("hola\nmundo") == "holamundo"


def test_no_toca_puntuacion_ni_numeros():
    assert normalize("¿Cuánto contamina PM2.5 hoy?") == "¿cuanto contamina pm2.5 hoy?"


def test_trunca_a_longitud_maxima():
    texto = "a" * 100
    assert normalize(texto, longitud_maxima=10) == "a" * 10


def test_intento_de_inyectar_marcador_interno():
    resultado = normalize(f"hola{_ENIE_PLACEHOLDER}mundo")
    assert "ñ" not in resultado
    assert resultado == "holamundo"


def test_es_funcion_pura_idempotente_en_su_propia_salida():
    texto = "El Año de la Contaminación en Cali"
    resultado = normalize(texto)
    assert normalize(resultado) == resultado
