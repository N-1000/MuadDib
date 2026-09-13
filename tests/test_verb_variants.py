from intent_router.lexicon import CONECTORES, NEGACIONES, VERBOS_ACCION
from intent_router.normalizer import normalize
from intent_router.verb_variants import VARIANTES_VERBO, resolver_verbo


def test_todos_los_valores_son_verbos_conocidos():
    for variante, infinitivo in VARIANTES_VERBO.items():
        assert infinitivo in VERBOS_ACCION, f"{variante!r} -> {infinitivo!r}"


def test_claves_y_valores_ya_normalizados():
    for variante, infinitivo in VARIANTES_VERBO.items():
        assert normalize(variante) == variante, f"clave sin normalizar: {variante!r}"
        assert normalize(infinitivo) == infinitivo, f"valor sin normalizar: {infinitivo!r}"


def test_ninguna_variante_es_ya_un_infinitivo():
    # si una clave coincide con un infinitivo, resolver_verbo() nunca la
    # usaria (el chequeo directo contra VERBOS_ACCION gana primero) y la
    # entrada quedaria muerta.
    assert VARIANTES_VERBO.keys().isdisjoint(VERBOS_ACCION)


def test_ninguna_variante_choca_con_conectores_ni_negaciones():
    assert VARIANTES_VERBO.keys().isdisjoint(CONECTORES)
    assert VARIANTES_VERBO.keys().isdisjoint(NEGACIONES)


def test_preposicion_para_no_esta_incluida():
    # "para" es la preposicion mas comun del idioma antes que el
    # imperativo voseo de "parar": se excluye a proposito.
    assert "para" not in VARIANTES_VERBO


def test_resolver_verbo_con_infinitivo_directo():
    assert resolver_verbo("mostrar") == "mostrar"


def test_resolver_verbo_con_imperativo_tu():
    assert resolver_verbo("muestra") == "mostrar"
    assert resolver_verbo("cancela") == "cancelar"


def test_resolver_verbo_con_voseo_que_diverge_del_tu():
    assert resolver_verbo("mostra") == "mostrar"
    assert resolver_verbo("encontra") == "encontrar"


def test_resolver_verbo_con_forma_me_pegada():
    assert resolver_verbo("mostrame") == "mostrar"
    assert resolver_verbo("dame") == "dar"
    assert resolver_verbo("ayudame") == "ayudar"


def test_resolver_verbo_con_modal_en_primera_persona():
    assert resolver_verbo("quiero") == "querer"
    assert resolver_verbo("necesito") == "necesitar"
    assert resolver_verbo("puedo") == "poder"
    assert resolver_verbo("debo") == "deber"


def test_resolver_verbo_con_ene_preservada():
    assert resolver_verbo("añade") == "añadir"


def test_resolver_verbo_con_forma_usted():
    assert resolver_verbo("deme") == "dar"


def test_resolver_verbo_palabra_desconocida_da_none():
    assert resolver_verbo("banana") is None
    assert resolver_verbo("") is None


def test_ver_no_tiene_variantes_por_ambiguedad():
    assert resolver_verbo("ve") is None
