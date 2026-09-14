"""Carga y valida config.yaml + rules_nivel0.yaml para construir el config de resolve()."""

from pathlib import Path
from typing import Any

import yaml

CAMPOS_ROUTING = ("threshold", "min_margin")


class ConfigError(Exception):
    """Config invalida detectada al arranque: el servicio no debe iniciar."""


def cargar_config(config_path: Path, rules_path: Path) -> dict[str, Any]:
    """Lee, valida y fusiona config.yaml y rules_nivel0.yaml en el dict que espera resolve()."""
    config_data = _leer_yaml(config_path)
    rules_data = _leer_yaml(rules_path)
    return {
        "client": _validar_client(config_data, config_path),
        "routing": _validar_routing(config_data, config_path),
        "intents": _validar_intents(rules_data, rules_path),
        "entity_catalog": rules_data.get("entity_catalog", {}),
    }


def _leer_yaml(path: Path) -> dict[str, Any]:
    """Lee un archivo YAML y exige que la raiz sea un mapping."""
    if not path.is_file():
        raise ConfigError(f"No existe el archivo de config: {path}")
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise ConfigError(f"{path}: el YAML raiz debe ser un mapping")
    return data


def _validar_client(data: dict[str, Any], path: Path) -> str:
    """Exige un 'client' no vacio."""
    client = data.get("client")
    if not isinstance(client, str) or not client:
        raise ConfigError(f"{path}: 'client' es obligatorio y debe ser un string no vacio")
    return client


def _validar_routing(data: dict[str, Any], path: Path) -> dict[str, float]:
    """Exige la seccion 'routing' completa, sin defaults implicitos."""
    routing = data.get("routing")
    if not isinstance(routing, dict):
        raise ConfigError(f"{path}: falta la seccion 'routing' obligatoria")
    return {campo: _validar_umbral(routing, campo, path) for campo in CAMPOS_ROUTING}


def _validar_umbral(routing: dict[str, Any], campo: str, path: Path) -> float:
    """Exige que routing[campo] sea numerico y este en [0.0, 1.0]."""
    if campo not in routing:
        raise ConfigError(f"{path}: falta 'routing.{campo}' obligatorio")
    valor = routing[campo]
    if isinstance(valor, bool) or not isinstance(valor, (int, float)):
        raise ConfigError(f"{path}: 'routing.{campo}' debe ser numerico, recibido {valor!r}")
    if not 0.0 <= valor <= 1.0:
        raise ConfigError(f"{path}: 'routing.{campo}' fuera de rango [0.0, 1.0]: {valor}")
    return float(valor)


def _validar_intents(data: dict[str, Any], path: Path) -> list[dict[str, Any]]:
    """Exige 'intents' no vacio con nombres unicos."""
    intents = data.get("intents")
    if not isinstance(intents, list) or not intents:
        raise ConfigError(f"{path}: falta 'intents' obligatorio o esta vacio")
    nombres_vistos: set[str] = set()
    for intent in intents:
        nombre = _validar_nombre_intent(intent, path)
        if nombre in nombres_vistos:
            raise ConfigError(f"{path}: intent duplicado '{nombre}'")
        nombres_vistos.add(nombre)
    return intents


def _validar_nombre_intent(intent: Any, path: Path) -> str:
    """Exige que la entrada sea un mapping con 'name' no vacio."""
    if not isinstance(intent, dict):
        raise ConfigError(f"{path}: entrada de intent invalida: {intent!r}")
    nombre = intent.get("name")
    if not isinstance(nombre, str) or not nombre:
        raise ConfigError(f"{path}: intent sin 'name' valido: {intent!r}")
    return nombre
