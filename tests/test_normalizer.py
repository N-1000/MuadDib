from intent_router.normalizer import _ENIE_PLACEHOLDER, normalize


def test_ene_con_tilde_mayuscula():
    assert normalize("Ñoño") == "ñoño"


def test_quita_acentos_normales():
    assert normalize("café") == "cafe"
    assert normalize("acción") == "accion"
    assert normalize("múltiple") == "multiple"


def test_quita_caracteres_de_control():
    assert normalize("hola\tmundo") == "holamundo"
    assert normalize("hola\nmundo") == "holamundo"


def test_no_toca_puntuacion_ni_numeros():
    assert normalize("¿Cuánto contamina PM2.5 hoy?") == "¿cuanto contamina pm2.5 hoy?"


def test_no_toca_emojis():
    assert normalize("hola 😀 mundo") == "hola 😀 mundo"
    assert normalize("📊📈 reporte") == "📊📈 reporte"


def test_selector_de_variacion_se_pierde_como_cualquier_mn():
    # El emoji de advertencia con estilo emoji son dos codepoints: la
    # advertencia (So) + un selector de variacion (U+FE0F, categoria
    # Mn). normalize() lo saca junto con
    # los acentos porque es exactamente lo que hace: sacar todo lo Mn.
    # El emoji base sobrevive; el selector no tiene valor semantico para
    # clasificar intencion, asi que no hace falta protegerlo.
    entrada = "\u26a0\ufe0f atenci\u00f3n"
    assert len(entrada) == 11
    assert normalize(entrada) == "\u26a0 atencion"


def test_emoji_no_rompe_idempotencia():
    texto = normalize("el aire está 🟡 hoy, ojo 👀")
    assert normalize(texto) == texto


def test_trunca_a_longitud_maxima():
    texto = "a" * 100
    assert normalize(texto, longitud_maxima=10) == "a" * 10


def test_intento_de_inyectar_marcador_interno():
    resultado = normalize(f"hola{_ENIE_PLACEHOLDER}mundo")
    assert "ñ" not in resultado
    assert resultado == "holamundo"
