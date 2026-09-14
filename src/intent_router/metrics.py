"""Logging estructurado y metricas agregadas de las decisiones del router."""

import logging
from dataclasses import dataclass

from intent_router.router import Decision

logger = logging.getLogger(__name__)

_NIVELES_RESUELTOS_LOCALMENTE = (0, 1)


@dataclass(frozen=True)
class EventoDecision:
    decision: Decision
    latencia_ms: float


_eventos: list[EventoDecision] = []


def log_decision(evento: EventoDecision) -> None:
    """Registra el evento en el logger estructurado y lo acumula para hit_rate()."""
    d = evento.decision
    logger.info(
        "decision_router",
        extra={
            "nivel": d.nivel,
            "intencion": d.intencion,
            "confianza": d.confianza,
            "entidades": d.entidades,
            "latencia_ms": evento.latencia_ms,
        },
    )
    _eventos.append(evento)


def hit_rate() -> float:
    """Fraccion de eventos registrados que se resolvieron sin escalar a Nivel 2 (LLM)."""
    if not _eventos:
        return 0.0
    resueltos = sum(
        1 for e in _eventos if e.decision.nivel in _NIVELES_RESUELTOS_LOCALMENTE
    )
    return resueltos / len(_eventos)


def reset() -> None:
    """Vacia el acumulador de metricas; uso principal en tests."""
    _eventos.clear()
