"""Referencia de como un cliente real cablea config_loader + resolve() + metrics.log_decision()."""

import time
from pathlib import Path

import yaml
from intent_router.config_loader import cargar_config
from intent_router.embeddings import MODEL_DEFAULT, load_model, precompute_canonical
from intent_router.metrics import EventoDecision, log_decision
from intent_router.router import RoutingResult, resolve

CONFIG_PATH = Path(__file__).resolve().parent / "clients" / "ecopulse" / "config.yaml"
RULES_PATH = Path(__file__).resolve().parent / "clients" / "ecopulse" / "rules_nivel0.yaml"
ENTITIES_PATH = Path(__file__).resolve().parent / "clients" / "ecopulse" / "entities.yaml"
CANONICAL_PATH = Path(__file__).resolve().parent / "clients" / "ecopulse" / "canonical.yaml"


class MotorRouter:
    """Agrupa la config y los embeddings canonicos ya precargados, listos para procesar mensajes."""

    def __init__(self, config: dict, canonical_data) -> None:
        self._config = config
        self._canonical_data = canonical_data

    def procesar_mensaje(self, mensaje: str) -> RoutingResult:
        """Resuelve un mensaje y registra cada clausula resultante en metrics.py."""
        inicio = time.perf_counter()
        resultado = resolve(mensaje, self._config, self._canonical_data)
        latencia_ms = (time.perf_counter() - inicio) * 1000
        for decision in resultado.decisiones:
            log_decision(EventoDecision(decision=decision, latencia_ms=latencia_ms))
        return resultado


def iniciar() -> MotorRouter:
    """Carga config, modelo y embeddings canonicos una sola vez al arranque, nunca por mensaje."""
    config = cargar_config(CONFIG_PATH, RULES_PATH, ENTITIES_PATH)
    modelo = load_model(MODEL_DEFAULT)
    canonical_data = _cargar_canonical(modelo) if modelo is not None else None
    return MotorRouter(config, canonical_data)


def _cargar_canonical(modelo):
    with open(CANONICAL_PATH, "r", encoding="utf-8") as f:
        canonical_yaml = yaml.safe_load(f)
    return precompute_canonical({"intents": canonical_yaml.get("intents", [])}, modelo)


def main() -> None:
    motor = iniciar()
    mensajes = [
        "Hola",
        "Compara la calidad del aire entre siloe y pance",
        "no quiero el reporte",
    ]
    for mensaje in mensajes:
        resultado = motor.procesar_mensaje(mensaje)
        for d in resultado.decisiones:
            print(
                f"'{d.clausula}' -> nivel={d.nivel} intencion={d.intencion} "
                f"candidato_descartado={d.candidato_descartado} accion={d.accion}"
            )


if __name__ == "__main__":
    main()
