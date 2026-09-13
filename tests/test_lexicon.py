from intent_router.lexicon import CONECTORES, NEGACIONES, VERBOS_ACCION
from intent_router.normalizer import normalize

_LISTAS = {
    "VERBOS_ACCION": VERBOS_ACCION,
    "CONECTORES": CONECTORES,
    "NEGACIONES": NEGACIONES,
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
    assert VERBOS_ACCION.isdisjoint(CONECTORES)
    assert VERBOS_ACCION.isdisjoint(NEGACIONES)
    assert CONECTORES.isdisjoint(NEGACIONES)


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


def test_negaciones_contiene_casos_esperados():
    for negacion in {"no", "nunca", "tampoco", "ni"}:
        assert negacion in NEGACIONES
