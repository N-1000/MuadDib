from pathlib import Path

import pytest
from intent_router.config_loader import ConfigError, cargar_config


def _escribir(path: Path, contenido: str) -> None:
    path.write_text(contenido, encoding="utf-8")


def _config_valido(tmp_path: Path) -> tuple[Path, Path]:
    config_path = tmp_path / "config.yaml"
    rules_path = tmp_path / "rules_nivel0.yaml"
    _escribir(
        config_path,
        "client: test\nrouting:\n  threshold: 0.80\n  min_margin: 0.10\n",
    )
    _escribir(
        rules_path,
        "client: test\nintents:\n"
        "  - name: saludo\n    phrases: [\"hola\"]\n    action: [\"reply\"]\n    sensitive: false\n",
    )
    return config_path, rules_path


def test_cargar_config_valido(tmp_path):
    config_path, rules_path = _config_valido(tmp_path)
    config = cargar_config(config_path, rules_path)
    assert config["client"] == "test"
    assert config["routing"] == {"threshold": 0.80, "min_margin": 0.10}
    assert config["intents"][0]["name"] == "saludo"


def test_archivo_inexistente_revienta(tmp_path):
    with pytest.raises(ConfigError):
        cargar_config(tmp_path / "no_existe.yaml", tmp_path / "tampoco.yaml")


def test_falta_seccion_routing_revienta(tmp_path):
    config_path, rules_path = _config_valido(tmp_path)
    _escribir(config_path, "client: test\n")
    with pytest.raises(ConfigError, match="routing"):
        cargar_config(config_path, rules_path)


def test_falta_threshold_revienta(tmp_path):
    config_path, rules_path = _config_valido(tmp_path)
    _escribir(config_path, "client: test\nrouting:\n  min_margin: 0.05\n")
    with pytest.raises(ConfigError, match="threshold"):
        cargar_config(config_path, rules_path)


def test_threshold_como_string_revienta(tmp_path):
    config_path, rules_path = _config_valido(tmp_path)
    _escribir(config_path, 'client: test\nrouting:\n  threshold: "0.60"\n  min_margin: 0.05\n')
    with pytest.raises(ConfigError, match="numerico"):
        cargar_config(config_path, rules_path)


def test_threshold_booleano_revienta(tmp_path):
    config_path, rules_path = _config_valido(tmp_path)
    _escribir(config_path, "client: test\nrouting:\n  threshold: true\n  min_margin: 0.05\n")
    with pytest.raises(ConfigError, match="numerico"):
        cargar_config(config_path, rules_path)


def test_min_margin_fuera_de_rango_revienta(tmp_path):
    config_path, rules_path = _config_valido(tmp_path)
    _escribir(config_path, "client: test\nrouting:\n  threshold: 0.60\n  min_margin: 1.5\n")
    with pytest.raises(ConfigError, match="rango"):
        cargar_config(config_path, rules_path)


def test_threshold_negativo_revienta(tmp_path):
    config_path, rules_path = _config_valido(tmp_path)
    _escribir(config_path, "client: test\nrouting:\n  threshold: -0.1\n  min_margin: 0.05\n")
    with pytest.raises(ConfigError, match="rango"):
        cargar_config(config_path, rules_path)


def test_falta_client_revienta(tmp_path):
    config_path, rules_path = _config_valido(tmp_path)
    _escribir(config_path, "routing:\n  threshold: 0.60\n  min_margin: 0.05\n")
    with pytest.raises(ConfigError, match="client"):
        cargar_config(config_path, rules_path)


def test_intents_vacio_revienta(tmp_path):
    config_path, rules_path = _config_valido(tmp_path)
    _escribir(rules_path, "client: test\nintents: []\n")
    with pytest.raises(ConfigError, match="intents"):
        cargar_config(config_path, rules_path)


def test_intent_sin_name_revienta(tmp_path):
    config_path, rules_path = _config_valido(tmp_path)
    _escribir(rules_path, 'client: test\nintents:\n  - phrases: ["hola"]\n')
    with pytest.raises(ConfigError, match="name"):
        cargar_config(config_path, rules_path)


def test_intent_duplicado_revienta(tmp_path):
    config_path, rules_path = _config_valido(tmp_path)
    _escribir(
        rules_path,
        "client: test\nintents:\n"
        "  - name: saludo\n    phrases: [\"hola\"]\n"
        "  - name: saludo\n    phrases: [\"chao\"]\n",
    )
    with pytest.raises(ConfigError, match="duplicado"):
        cargar_config(config_path, rules_path)


def test_yaml_raiz_no_es_mapping_revienta(tmp_path):
    config_path, rules_path = _config_valido(tmp_path)
    _escribir(config_path, "- item1\n- item2\n")
    with pytest.raises(ConfigError, match="mapping"):
        cargar_config(config_path, rules_path)
