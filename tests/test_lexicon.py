import itertools

from intent_router.lexicon import (
    CONECTORES,
    CONECTORES_COORDINANTES,
    DETERMINANTES,
    NEGACIONES,
    VERBOS_ACCION,
)
from intent_router.normalizer import normalize

_LISTAS = {
    "VERBOS_ACCION": VERBOS_ACCION,
    "CONECTORES": CONECTORES,
    "NEGACIONES": NEGACIONES,
    "CONECTORES_COORDINANTES": CONECTORES_COORDINANTES,
    "DETERMINANTES": DETERMINANTES,
}

_LISTAS_MUTUAMENTE_EXCLUYENTES = {
    "VERBOS_ACCION": VERBOS_ACCION,
    "CONECTORES": CONECTORES,
    "NEGACIONES": NEGACIONES,
    "DETERMINANTES": DETERMINANTES,
}


def test_listas_son_frozenset():
    for nombre, lista in _LISTAS.items():
        assert isinstance(lista, frozenset), nombre


def test_listas_no_vacias():
    for nombre, lista in _LISTAS.items():
        assert len(lista) > 0, nombre


def test_entradas_ya_normalizadas():
    for nombre, lista in _LISTAS.items():
        for palabra in lista:
            assert normalize(palabra) == palabra, f"{nombre}: {palabra!r}"


def test_entradas_son_una_sola_palabra():
    for nombre, lista in _LISTAS.items():
        for palabra in lista:
            assert " " not in palabra, f"{nombre}: {palabra!r}"


def test_listas_disjuntas_entre_si():
    for (na, a), (nb, b) in itertools.combinations(_LISTAS_MUTUAMENTE_EXCLUYENTES.items(), 2):
        assert a.isdisjoint(b), f"{na} y {nb} se solapan: {a & b}"


def test_conectores_coordinantes_es_subconjunto_de_conectores():
    assert CONECTORES_COORDINANTES <= CONECTORES


def test_conectores_coordinantes_no_incluye_subordinantes():
    for subordinante in {"aunque", "mientras", "despues", "luego", "entonces"}:
        assert subordinante not in CONECTORES_COORDINANTES


def test_verbos_accion_contiene_casos_esperados():
    for verbo in {"mostrar", "cancelar", "activar", "consultar"}:
        assert verbo in VERBOS_ACCION


def test_verbo_con_ene_preserva_la_ene():
    # Regresion: "anadir" (sin ñ) no es la palabra real y normalize()
    # nunca la produce, porque preserva la ñ.
    assert "añadir" in VERBOS_ACCION
    assert "anadir" not in VERBOS_ACCION


def test_conectores_contiene_casos_esperados():
    for conector in {"y", "pero", "tambien", "o"}:
        assert conector in CONECTORES


def test_conectores_coordinantes_contiene_casos_esperados():
    for conector in {"y", "pero", "tambien", "o"}:
        assert conector in CONECTORES_COORDINANTES


def test_negaciones_contiene_casos_esperados():
    for negacion in {"no", "nunca", "tampoco", "ni"}:
        assert negacion in NEGACIONES


def test_determinantes_contiene_casos_esperados():
    for determinante in {"el", "la", "los", "las", "un", "una"}:
        assert determinante in DETERMINANTES
