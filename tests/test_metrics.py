import logging

import pytest
from intent_router.metrics import EventoDecision, hit_rate, log_decision, reset
from intent_router.router import Decision


@pytest.fixture(autouse=True)
def _limpiar_acumulador():
    reset()
    yield
    reset()


def _decision(nivel: int, intencion: str = "consultar_aire") -> Decision:
    return Decision(
        intencion=intencion,
        nivel=nivel,
        confianza=0.9,
        accion=("show_air",) if nivel < 2 else ("escalate_to_llm",),
        sensitive=False,
        entidades={"region": "pance"},
    )


def test_hit_rate_sin_eventos_es_cero():
    assert hit_rate() == 0.0


def test_log_decision_acumula_para_hit_rate():
    log_decision(EventoDecision(decision=_decision(0), latencia_ms=1.2))
    log_decision(EventoDecision(decision=_decision(1), latencia_ms=3.4))
    log_decision(EventoDecision(decision=_decision(2), latencia_ms=5.6))

    assert hit_rate() == pytest.approx(2 / 3)


def test_hit_rate_todo_resuelto_localmente():
    log_decision(EventoDecision(decision=_decision(0), latencia_ms=1.0))
    log_decision(EventoDecision(decision=_decision(1), latencia_ms=1.0))
    assert hit_rate() == 1.0


def test_hit_rate_todo_escalado():
    log_decision(EventoDecision(decision=_decision(2), latencia_ms=1.0))
    log_decision(EventoDecision(decision=_decision(2), latencia_ms=1.0))
    assert hit_rate() == 0.0


def test_reset_vacia_el_acumulador():
    log_decision(EventoDecision(decision=_decision(0), latencia_ms=1.0))
    assert hit_rate() == 1.0
    reset()
    assert hit_rate() == 0.0


def test_log_decision_emite_registro_estructurado(caplog):
    with caplog.at_level(logging.INFO, logger="intent_router.metrics"):
        log_decision(EventoDecision(decision=_decision(1, "consultar_pronostico"), latencia_ms=42.5))

    assert len(caplog.records) == 1
    registro = caplog.records[0]
    assert registro.nivel == 1
    assert registro.intencion == "consultar_pronostico"
    assert registro.confianza == 0.9
    assert registro.entidades == {"region": "pance"}
    assert registro.latencia_ms == 42.5
