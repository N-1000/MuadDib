from intent_router.entities import extract_entities

_CONFIG = {
    "entity_catalog": {
        "region": [
            {"value": "pance", "keywords": ["pance"]},
            {"value": "sur", "keywords": ["sur", "ciudad jardin"]},
            {"value": "centro", "keywords": ["centro"]},
        ],
        "node": [
            {"value": "node-pance", "keywords": ["nodo pance"]},
        ],
    }
}


def test_detecta_una_entidad():
    assert extract_entities("como esta el aire en pance", _CONFIG) == {"region": ["pance"]}


def test_detecta_dos_entidades_del_mismo_tipo():
    resultado = extract_entities("compara pance con el centro", _CONFIG)
    assert resultado == {"region": ["pance", "centro"]}


def test_detecta_entidades_de_tipos_distintos():
    resultado = extract_entities("dame el estado del nodo pance", _CONFIG)
    assert resultado == {"region": ["pance"], "node": ["node-pance"]}


def test_sin_match_devuelve_dict_vacio():
    assert extract_entities("hola como estas", _CONFIG) == {}


def test_texto_vacio_devuelve_dict_vacio():
    assert extract_entities("", _CONFIG) == {}


def test_no_duplica_valor_si_matchean_varias_keywords_de_la_misma_entrada():
    config = {
        "entity_catalog": {
            "region": [{"value": "sur", "keywords": ["sur", "ciudad jardin"]}],
        }
    }
    resultado = extract_entities("el sur y ciudad jardin", config)
    assert resultado == {"region": ["sur"]}


def test_config_sin_entity_catalog_devuelve_dict_vacio():
    assert extract_entities("pance", {}) == {}


def test_usa_keywords_normalizadas_precalculadas_en_vez_de_las_crudas():
    config = {
        "entity_catalog": {
            "region": [{"value": "pance", "keywords": ["esto no importa"], "keywords_normalizadas": ("pance",)}],
        }
    }
    assert extract_entities("el aire en pance", config) == {"region": ["pance"]}
    assert extract_entities("esto no importa", config) == {}
