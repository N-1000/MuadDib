import pytest
from intent_router.config_loader import ConfigError
from intent_router.tools import (
    Herramienta,
    validar_acciones_registradas,
    validar_coherencia_sensitive_efecto,
    validar_esquemas_herramientas,
    validar_input_herramienta,
)


def _herramienta(name: str, efecto_real: bool = False, parametros: dict | None = None) -> Herramienta:
    return Herramienta(
        name=name,
        description=f"descripcion de {name}",
        parametros=parametros or {"type": "object", "properties": {"region": {"type": "string"}}, "required": ["region"]},
        funcion=lambda **kwargs: kwargs,
        efecto_real=efecto_real,
    )


def test_validar_esquemas_herramientas_esquema_valido_no_revienta():
    validar_esquemas_herramientas((_herramienta("show_air"),))


def test_validar_esquemas_herramientas_esquema_invalido_revienta():
    rota = _herramienta("show_air", parametros={"type": "object", "properties": {"region": {"type": "no_existe"}}})
    with pytest.raises(ConfigError, match="show_air"):
        validar_esquemas_herramientas((rota,))


def test_validar_acciones_registradas_todas_presentes_no_revienta():
    config = {"acciones_declaradas": frozenset({"show_air", "show_trend"})}
    validar_acciones_registradas(config, (_herramienta("show_air"), _herramienta("show_trend")))


def test_validar_acciones_registradas_falta_una_revienta():
    config = {"acciones_declaradas": frozenset({"show_air", "show_trend"})}
    with pytest.raises(ConfigError, match="show_trend"):
        validar_acciones_registradas(config, (_herramienta("show_air"),))


def test_validar_coherencia_sensitive_efecto_coherente_no_revienta():
    config = {"acciones_sensibles": frozenset({"send_alert"})}
    validar_coherencia_sensitive_efecto(config, (_herramienta("send_alert", efecto_real=True),))


def test_validar_coherencia_sensitive_efecto_incoherente_revienta():
    config = {"acciones_sensibles": frozenset({"send_alert"})}
    with pytest.raises(ConfigError, match="send_alert"):
        validar_coherencia_sensitive_efecto(config, (_herramienta("send_alert", efecto_real=False),))


def test_validar_coherencia_sensitive_efecto_ignora_accion_no_registrada():
    config = {"acciones_sensibles": frozenset({"accion_sin_herramienta"})}
    validar_coherencia_sensitive_efecto(config, (_herramienta("otra_cosa", efecto_real=False),))


def test_validar_input_herramienta_input_valido():
    h = _herramienta("show_air")
    assert validar_input_herramienta(h, {"region": "pance"}) is True


def test_validar_input_herramienta_rechaza_clave_extra():
    h = _herramienta("show_air")
    assert validar_input_herramienta(h, {"region": "pance", "inyeccion": "borrar_todo"}) is False


def test_validar_input_herramienta_rechaza_tipo_incorrecto():
    h = _herramienta("show_air")
    assert validar_input_herramienta(h, {"region": 123}) is False


def test_validar_input_herramienta_rechaza_campo_requerido_faltante():
    h = _herramienta("show_air")
    assert validar_input_herramienta(h, {}) is False
