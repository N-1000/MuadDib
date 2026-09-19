from pathlib import Path

import pytest
from intent_router.config_loader import ConfigError, cargar_config


def _escribir(path: Path, contenido: str) -> None:
    path.write_text(contenido, encoding="utf-8")


def _config_valido(tmp_path: Path) -> tuple[Path, Path, Path]:
    config_path = tmp_path / "config.yaml"
    rules_path = tmp_path / "rules_nivel0.yaml"
    entities_path = tmp_path / "entities.yaml"
    _escribir(
        config_path,
        "client: test\nrouting:\n  threshold: 0.80\n  min_margin: 0.10\n",
    )
    _escribir(
        rules_path,
        "client: test\nintents:\n"
        "  - name: saludo\n    phrases: [\"hola\"]\n    action: [\"reply\"]\n    sensitive: false\n",
    )
    _escribir(
        entities_path,
        "client: test\nentity_catalog:\n"
        "  region:\n    - value: pance\n      keywords: [\"pance\"]\n",
    )
    return config_path, rules_path, entities_path


def test_cargar_config_valido(tmp_path):
    config_path, rules_path, entities_path = _config_valido(tmp_path)
    config = cargar_config(config_path, rules_path, entities_path)
    assert config["client"] == "test"
    assert config["routing"] == {"threshold": 0.80, "min_margin": 0.10}
    assert config["intents"][0]["name"] == "saludo"
    assert config["entity_catalog"]["region"][0]["value"] == "pance"


def test_archivo_inexistente_revienta(tmp_path):
    with pytest.raises(ConfigError):
        cargar_config(tmp_path / "no_existe.yaml", tmp_path / "tampoco.yaml", tmp_path / "ni_esto.yaml")


def test_falta_seccion_routing_revienta(tmp_path):
    config_path, rules_path, entities_path = _config_valido(tmp_path)
    _escribir(config_path, "client: test\n")
    with pytest.raises(ConfigError, match="routing"):
        cargar_config(config_path, rules_path, entities_path)


def test_falta_threshold_revienta(tmp_path):
    config_path, rules_path, entities_path = _config_valido(tmp_path)
    _escribir(config_path, "client: test\nrouting:\n  min_margin: 0.05\n")
    with pytest.raises(ConfigError, match="threshold"):
        cargar_config(config_path, rules_path, entities_path)


def test_threshold_como_string_revienta(tmp_path):
    config_path, rules_path, entities_path = _config_valido(tmp_path)
    _escribir(config_path, 'client: test\nrouting:\n  threshold: "0.60"\n  min_margin: 0.05\n')
    with pytest.raises(ConfigError, match="numerico"):
        cargar_config(config_path, rules_path, entities_path)


def test_threshold_booleano_revienta(tmp_path):
    config_path, rules_path, entities_path = _config_valido(tmp_path)
    _escribir(config_path, "client: test\nrouting:\n  threshold: true\n  min_margin: 0.05\n")
    with pytest.raises(ConfigError, match="numerico"):
        cargar_config(config_path, rules_path, entities_path)


def test_min_margin_fuera_de_rango_revienta(tmp_path):
    config_path, rules_path, entities_path = _config_valido(tmp_path)
    _escribir(config_path, "client: test\nrouting:\n  threshold: 0.60\n  min_margin: 1.5\n")
    with pytest.raises(ConfigError, match="rango"):
        cargar_config(config_path, rules_path, entities_path)


def test_threshold_negativo_revienta(tmp_path):
    config_path, rules_path, entities_path = _config_valido(tmp_path)
    _escribir(config_path, "client: test\nrouting:\n  threshold: -0.1\n  min_margin: 0.05\n")
    with pytest.raises(ConfigError, match="rango"):
        cargar_config(config_path, rules_path, entities_path)


def test_falta_client_revienta(tmp_path):
    config_path, rules_path, entities_path = _config_valido(tmp_path)
    _escribir(config_path, "routing:\n  threshold: 0.60\n  min_margin: 0.05\n")
    with pytest.raises(ConfigError, match="client"):
        cargar_config(config_path, rules_path, entities_path)


def test_intents_vacio_revienta(tmp_path):
    config_path, rules_path, entities_path = _config_valido(tmp_path)
    _escribir(rules_path, "client: test\nintents: []\n")
    with pytest.raises(ConfigError, match="intents"):
        cargar_config(config_path, rules_path, entities_path)


def test_intent_sin_name_revienta(tmp_path):
    config_path, rules_path, entities_path = _config_valido(tmp_path)
    _escribir(rules_path, 'client: test\nintents:\n  - phrases: ["hola"]\n')
    with pytest.raises(ConfigError, match="name"):
        cargar_config(config_path, rules_path, entities_path)


def test_intent_duplicado_revienta(tmp_path):
    config_path, rules_path, entities_path = _config_valido(tmp_path)
    _escribir(
        rules_path,
        "client: test\nintents:\n"
        "  - name: saludo\n    phrases: [\"hola\"]\n"
        "  - name: saludo\n    phrases: [\"chao\"]\n",
    )
    with pytest.raises(ConfigError, match="duplicado"):
        cargar_config(config_path, rules_path, entities_path)


def test_yaml_raiz_no_es_mapping_revienta(tmp_path):
    config_path, rules_path, entities_path = _config_valido(tmp_path)
    _escribir(config_path, "- item1\n- item2\n")
    with pytest.raises(ConfigError, match="mapping"):
        cargar_config(config_path, rules_path, entities_path)


def test_entity_catalog_vacio_revienta(tmp_path):
    config_path, rules_path, entities_path = _config_valido(tmp_path)
    _escribir(entities_path, "client: test\nentity_catalog: {}\n")
    with pytest.raises(ConfigError, match="entity_catalog"):
        cargar_config(config_path, rules_path, entities_path)


def test_entity_catalog_tipo_vacio_revienta(tmp_path):
    config_path, rules_path, entities_path = _config_valido(tmp_path)
    _escribir(entities_path, "client: test\nentity_catalog:\n  region: []\n")
    with pytest.raises(ConfigError, match="region"):
        cargar_config(config_path, rules_path, entities_path)


def test_entity_catalog_entrada_sin_value_revienta(tmp_path):
    config_path, rules_path, entities_path = _config_valido(tmp_path)
    _escribir(entities_path, 'client: test\nentity_catalog:\n  region:\n    - keywords: ["pance"]\n')
    with pytest.raises(ConfigError, match="value"):
        cargar_config(config_path, rules_path, entities_path)


def test_entity_catalog_entrada_sin_keywords_revienta(tmp_path):
    config_path, rules_path, entities_path = _config_valido(tmp_path)
    _escribir(entities_path, "client: test\nentity_catalog:\n  region:\n    - value: pance\n      keywords: []\n")
    with pytest.raises(ConfigError, match="keywords"):
        cargar_config(config_path, rules_path, entities_path)


def test_entity_catalog_value_duplicado_revienta(tmp_path):
    config_path, rules_path, entities_path = _config_valido(tmp_path)
    _escribir(
        entities_path,
        "client: test\nentity_catalog:\n  region:\n"
        "    - value: pance\n      keywords: [\"pance\"]\n"
        "    - value: pance\n      keywords: [\"otra\"]\n",
    )
    with pytest.raises(ConfigError, match="duplicado"):
        cargar_config(config_path, rules_path, entities_path)


def test_entity_defaults_ausente_devuelve_dict_vacio(tmp_path):
    config_path, rules_path, entities_path = _config_valido(tmp_path)
    config = cargar_config(config_path, rules_path, entities_path)
    assert config["entity_defaults"] == {}


def test_entity_defaults_valido_se_propaga(tmp_path):
    config_path, rules_path, entities_path = _config_valido(tmp_path)
    _escribir(
        config_path,
        "client: test\nrouting:\n  threshold: 0.80\n  min_margin: 0.10\n"
        "entity_defaults:\n  region: pance\n",
    )
    config = cargar_config(config_path, rules_path, entities_path)
    assert config["entity_defaults"] == {"region": "pance"}


def test_entity_defaults_no_es_mapping_revienta(tmp_path):
    config_path, rules_path, entities_path = _config_valido(tmp_path)
    _escribir(
        config_path,
        "client: test\nrouting:\n  threshold: 0.80\n  min_margin: 0.10\n"
        "entity_defaults: [\"region\"]\n",
    )
    with pytest.raises(ConfigError, match="entity_defaults"):
        cargar_config(config_path, rules_path, entities_path)


def test_entity_defaults_tipo_inexistente_en_catalogo_revienta(tmp_path):
    config_path, rules_path, entities_path = _config_valido(tmp_path)
    _escribir(
        config_path,
        "client: test\nrouting:\n  threshold: 0.80\n  min_margin: 0.10\n"
        "entity_defaults:\n  periodo: 24h\n",
    )
    with pytest.raises(ConfigError, match="periodo"):
        cargar_config(config_path, rules_path, entities_path)


def test_entity_defaults_value_inexistente_en_catalogo_revienta(tmp_path):
    config_path, rules_path, entities_path = _config_valido(tmp_path)
    _escribir(
        config_path,
        "client: test\nrouting:\n  threshold: 0.80\n  min_margin: 0.10\n"
        "entity_defaults:\n  region: siloe\n",
    )
    with pytest.raises(ConfigError, match="region"):
        cargar_config(config_path, rules_path, entities_path)
