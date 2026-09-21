"""Carga y valida config.yaml + rules_nivel0.yaml + entities.yaml para construir el config de resolve()."""

from pathlib import Path
from typing import Any

import yaml

CAMPOS_ROUTING = ("threshold", "min_margin")


class ConfigError(Exception):
    """Config invalida detectada al arranque: el servicio no debe iniciar."""


def cargar_config(config_path: Path, rules_path: Path, entities_path: Path, canonical_path: Path) -> dict[str, Any]:
    """Lee, valida y fusiona config.yaml, rules_nivel0.yaml y entities.yaml en el dict que espera resolve()."""
    config_data = _leer_yaml(config_path)
    rules_data = _leer_yaml(rules_path)
    entities_data = _leer_yaml(entities_path)
    canonical_data = _leer_yaml(canonical_path)
    entity_catalog = _validar_entity_catalog(entities_data, entities_path)
    intents = _validar_intents(rules_data, rules_path)
    _validar_consistencia_accion(intents, canonical_data, rules_path, canonical_path)
    acciones_declaradas, acciones_sensibles = _derivar_acciones(intents, canonical_data.get("intents", []))
    return {
        "client": _validar_client(config_data, config_path),
        "routing": _validar_routing(config_data, config_path),
        "intents": intents,
        "entity_catalog": entity_catalog,
        "entity_defaults": _validar_entity_defaults(config_data, entity_catalog, config_path, entities_path),
        "nivel2": _validar_nivel2(config_data, config_path),
        "acciones_declaradas": acciones_declaradas,
        "acciones_sensibles": acciones_sensibles,
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


def _validar_entity_catalog(data: dict[str, Any], path: Path) -> dict[str, list[dict[str, Any]]]:
    """Exige 'entity_catalog' como mapping de tipo -> lista de {value, keywords}."""
    catalogo = data.get("entity_catalog")
    if not isinstance(catalogo, dict) or not catalogo:
        raise ConfigError(f"{path}: falta 'entity_catalog' obligatorio o esta vacio")
    return {tipo: _validar_entradas_tipo(tipo, entradas, path) for tipo, entradas in catalogo.items()}


def _validar_entradas_tipo(tipo: str, entradas: Any, path: Path) -> list[dict[str, Any]]:
    """Exige que las entradas de un tipo de entidad sean una lista no vacia de {value, keywords}."""
    if not isinstance(entradas, list) or not entradas:
        raise ConfigError(f"{path}: entity_catalog.{tipo} debe ser una lista no vacia")
    valores_vistos: set[str] = set()
    for entrada in entradas:
        valor = _validar_entrada_entidad(tipo, entrada, path)
        if valor in valores_vistos:
            raise ConfigError(f"{path}: entity_catalog.{tipo} tiene 'value' duplicado '{valor}'")
        valores_vistos.add(valor)
    return entradas


def _validar_entrada_entidad(tipo: str, entrada: Any, path: Path) -> str:
    """Exige que la entrada tenga 'value' no vacio y 'keywords' como lista no vacia de strings."""
    if not isinstance(entrada, dict):
        raise ConfigError(f"{path}: entity_catalog.{tipo} tiene una entrada invalida: {entrada!r}")
    valor = entrada.get("value")
    if not isinstance(valor, str) or not valor:
        raise ConfigError(f"{path}: entity_catalog.{tipo} tiene una entrada sin 'value' valido: {entrada!r}")
    keywords = entrada.get("keywords")
    if not isinstance(keywords, list) or not keywords or not all(isinstance(k, str) and k for k in keywords):
        raise ConfigError(f"{path}: entity_catalog.{tipo}.{valor} necesita 'keywords' como lista no vacia de strings")
    return valor


def _validar_consistencia_accion(
    rules_intents: list[dict[str, Any]],
    canonical_data: dict[str, Any],
    rules_path: Path,
    canonical_path: Path,
) -> None:
    """Exige que un mismo intent name declare la misma action en rules_nivel0.yaml y canonical.yaml."""
    acciones_canonical = {
        intent["name"]: tuple(intent.get("action", []))
        for intent in canonical_data.get("intents", [])
        if isinstance(intent, dict) and isinstance(intent.get("name"), str)
    }
    for intent in rules_intents:
        nombre = intent["name"]
        if nombre not in acciones_canonical:
            continue
        accion_rules = tuple(intent.get("action", []))
        accion_canonical = acciones_canonical[nombre]
        if accion_rules != accion_canonical:
            raise ConfigError(
                f"'{nombre}' declara action distinta en {rules_path} ({list(accion_rules)}) "
                f"y en {canonical_path} ({list(accion_canonical)})"
            )


def _derivar_acciones(
    rules_intents: list[dict[str, Any]],
    canonical_intents: list[dict[str, Any]],
) -> tuple[frozenset[str], frozenset[str]]:
    """Deriva el set de todas las acciones declaradas y el subset que pertenece a un intent sensitive:true."""
    declaradas: set[str] = set()
    sensibles: set[str] = set()
    for intent in (*rules_intents, *canonical_intents):
        if not isinstance(intent, dict):
            continue
        acciones = intent.get("action", [])
        if not isinstance(acciones, list):
            continue
        declaradas.update(acciones)
        if intent.get("sensitive") is True:
            sensibles.update(acciones)
    return frozenset(declaradas), frozenset(sensibles)


def _validar_nivel2(data: dict[str, Any], path: Path) -> dict[str, Any]:
    """Exige la seccion 'nivel2' completa, sin defaults implicitos."""
    nivel2 = data.get("nivel2")
    if not isinstance(nivel2, dict):
        raise ConfigError(f"{path}: falta la seccion 'nivel2' obligatoria")
    return {
        "timeout_s": _validar_positivo(nivel2, "timeout_s", path),
        "max_vueltas_tool_use": int(_validar_positivo(nivel2, "max_vueltas_tool_use", path)),
        "max_tokens_respuesta": int(_validar_positivo(nivel2, "max_tokens_respuesta", path)),
        "max_caracteres_resultado_herramienta": int(
            _validar_positivo(nivel2, "max_caracteres_resultado_herramienta", path)
        ),
        "modelo": _validar_modelo_nivel2(nivel2, path),
    }


def _validar_positivo(nivel2: dict[str, Any], campo: str, path: Path) -> float:
    """Exige que nivel2[campo] sea numerico y mayor a cero."""
    if campo not in nivel2:
        raise ConfigError(f"{path}: falta 'nivel2.{campo}' obligatorio")
    valor = nivel2[campo]
    if isinstance(valor, bool) or not isinstance(valor, (int, float)):
        raise ConfigError(f"{path}: 'nivel2.{campo}' debe ser numerico, recibido {valor!r}")
    if valor <= 0:
        raise ConfigError(f"{path}: 'nivel2.{campo}' debe ser mayor a cero: {valor}")
    return float(valor)


def _validar_modelo_nivel2(nivel2: dict[str, Any], path: Path) -> str:
    """Exige que nivel2.modelo sea un string no vacio."""
    modelo = nivel2.get("modelo")
    if not isinstance(modelo, str) or not modelo:
        raise ConfigError(f"{path}: 'nivel2.modelo' es obligatorio y debe ser un string no vacio")
    return modelo


def _validar_entity_defaults(
    config_data: dict[str, Any],
    entity_catalog: dict[str, list[dict[str, Any]]],
    config_path: Path,
    entities_path: Path,
) -> dict[str, str]:
    """Exige que cada default declarado apunte a un tipo y value que existan en entity_catalog."""
    defaults = config_data.get("entity_defaults", {})
    if not isinstance(defaults, dict):
        raise ConfigError(f"{config_path}: 'entity_defaults' debe ser un mapping de tipo -> value")

    resultado: dict[str, str] = {}
    for tipo, valor in defaults.items():
        if not isinstance(valor, str) or not valor:
            raise ConfigError(f"{config_path}: entity_defaults.{tipo} debe ser un string no vacio")
        if tipo not in entity_catalog:
            raise ConfigError(
                f"{config_path}: entity_defaults.{tipo} declara un tipo que no existe en "
                f"entity_catalog ({entities_path})"
            )
        valores_validos = {entrada["value"] for entrada in entity_catalog[tipo]}
        if valor not in valores_validos:
            raise ConfigError(
                f"{config_path}: entity_defaults.{tipo}='{valor}' no es un value declarado en "
                f"entity_catalog.{tipo} ({entities_path})"
            )
        resultado[tipo] = valor
    return resultado
