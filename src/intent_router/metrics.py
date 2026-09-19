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


# Acumula desde el arranque del proceso, sin ventana ni descarte: hit_rate() es un promedio de toda
# la vida del proceso, no puede ver una tendencia reciente. Con diez mil eventos acumulados, cien
# escaladas seguidas mueven el promedio casi nada -- por eso una alerta de degradacion sobre este
# acumulador tal como esta no detecta nada. Antes de usar esto para alertar hace falta una ventana
# deslizante (ultimos N eventos o ultimos N minutos); no se construyo porque todavia no hay caller
# en produccion que la necesite.
_eventos: list[EventoDecision] = []


def log_decision(evento: EventoDecision) -> None:
    """Registra el evento en el logger estructurado y lo acumula para hit_rate()."""
    d = evento.decision
    logger.info(
        "decision_router",
        extra={
            "nivel": d.nivel,
            "intencion": d.intencion,
            "candidato_descartado": d.candidato_descartado,
            "confianza": d.confianza,
            "entidades": d.entidades,
            "entidades_default": d.entidades_default,
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
