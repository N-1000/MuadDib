from intent_router.lexicon import VERBOS_ACCION
from intent_router.typo_fallback import corregir_typo


def test_token_exacto_se_devuelve_sin_tocar():
    assert corregir_typo("mostrar", VERBOS_ACCION) == "mostrar"


def test_typo_de_una_letra_se_corrige():
    assert corregir_typo("mostar", VERBOS_ACCION) == "mostrar"


def test_typo_de_letra_repetida_se_corrige():
    assert corregir_typo("cancelaar", VERBOS_ACCION) == "cancelar"
    assert corregir_typo("activarr", VERBOS_ACCION) == "activar"


def test_palabra_no_relacionada_no_se_corrige():
    assert corregir_typo("xyz", VERBOS_ACCION) is None
    assert corregir_typo("perro", VERBOS_ACCION) is None


def test_umbral_bajo_corrige_lo_que_el_default_rechaza():
    # No depende del score exacto de rapidfuzz: umbral=0 acepta cualquier
    # mejor candidato, sea cual sea su ratio.
    token = "notificarrrrrr"
    assert corregir_typo(token, VERBOS_ACCION) is None
    assert corregir_typo(token, VERBOS_ACCION, umbral=0) == "notificar"


def test_vocabulario_vacio_no_rompe():
    assert corregir_typo("mostar", frozenset()) is None


def test_candidatos_ambiguos_devuelve_none():
    # "confirurar": configurar=90.0, confirmar=84.2, gap=5.8 < margen default (10).
    assert corregir_typo("confirurar", VERBOS_ACCION) is None


def test_ganador_claro_corrige_pese_a_segundo_candidato():
    # "mostar": mostrar=92.3, consultar=66.7, gap=25.6 >= margen default (10).
    assert corregir_typo("mostar", VERBOS_ACCION) == "mostrar"


def test_margen_ambiguedad_personalizado_es_mas_permisivo():
    assert corregir_typo("confirurar", VERBOS_ACCION, margen_ambiguedad=3) == "configurar"
