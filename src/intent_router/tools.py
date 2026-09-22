"""Registro de herramientas inyectadas por el cliente para el motor de Nivel 2."""

from dataclasses import dataclass
from typing import Any, Callable

import jsonschema

from intent_router.config_loader import ConfigError


@dataclass(frozen=True)
class Herramienta:
    name: str
    description: str
    parametros: dict[str, Any]
    funcion: Callable[..., Any]
    efecto_real: bool


def validar_esquemas_herramientas(herramientas: tuple[Herramienta, ...]) -> None:
    """Exige que el JSON schema de parametros de cada herramienta sea valido."""
    invalidas = []
    for herramienta in herramientas:
        try:
            jsonschema.Draft7Validator.check_schema(herramienta.parametros)
        except jsonschema.exceptions.SchemaError:
            invalidas.append(herramienta.name)
    if invalidas:
        raise ConfigError(f"Herramientas con JSON schema de parametros invalido: {sorted(invalidas)}")


def validar_acciones_registradas(config: dict[str, Any], herramientas: tuple[Herramienta, ...]) -> None:
    """Exige que toda accion declarada en rules_nivel0.yaml/canonical.yaml tenga una Herramienta registrada."""
    registradas = {h.name for h in herramientas}
    faltantes = config["acciones_declaradas"] - registradas
    if faltantes:
        raise ConfigError(f"Acciones declaradas sin herramienta registrada: {sorted(faltantes)}")


def validar_coherencia_sensitive_efecto(config: dict[str, Any], herramientas: tuple[Herramienta, ...]) -> None:
    """Exige que toda accion de un intent sensitive:true apunte a una herramienta con efecto_real=True."""
    registro = {h.name: h for h in herramientas}
    incoherentes = {
        nombre
        for nombre in config["acciones_sensibles"]
        if nombre in registro and not registro[nombre].efecto_real
    }
    if incoherentes:
        raise ConfigError(
            f"Intents sensitive:true declaran acciones cuya herramienta no tiene efecto_real=True: {sorted(incoherentes)}"
        )


def validar_input_herramienta(herramienta: Herramienta, entrada: dict[str, Any]) -> bool:
    """Valida entrada contra el JSON schema de la herramienta, rechazando claves no declaradas."""
    esquema = dict(herramienta.parametros)
    esquema["additionalProperties"] = False
    try:
        jsonschema.validate(instance=entrada, schema=esquema)
    except jsonschema.exceptions.ValidationError:
        return False
    return True
