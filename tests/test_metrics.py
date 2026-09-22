import logging

import pytest
from intent_router.metrics import (
    EventoDecision,
    desglose_por_intencion,
    desglose_por_nivel,
    hit_rate,
    log_decision,
    reset,
)
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


def test_desglose_por_nivel_sin_eventos_es_vacio():
    assert desglose_por_nivel() == {}


def test_desglose_por_nivel_cuenta_por_nivel():
    log_decision(EventoDecision(decision=_decision(0), latencia_ms=1.0))
    log_decision(EventoDecision(decision=_decision(0), latencia_ms=1.0))
    log_decision(EventoDecision(decision=_decision(1), latencia_ms=1.0))
    log_decision(EventoDecision(decision=_decision(2), latencia_ms=1.0))

    assert desglose_por_nivel() == {0: 2, 1: 1, 2: 1}


def test_desglose_por_intencion_sin_eventos_es_vacio():
    assert desglose_por_intencion() == {}


def test_desglose_por_intencion_cuenta_por_intencion_y_agrupa_none():
    log_decision(EventoDecision(decision=_decision(0, "consultar_aire"), latencia_ms=1.0))
    log_decision(EventoDecision(decision=_decision(0, "consultar_aire"), latencia_ms=1.0))
    log_decision(EventoDecision(decision=_decision(1, "localizar_sensor"), latencia_ms=1.0))
    log_decision(
        EventoDecision(
            decision=Decision(intencion=None, nivel=2, confianza=0.0, accion=("escalate_to_llm",), sensitive=False),
            latencia_ms=1.0,
        )
    )

    assert desglose_por_intencion() == {"consultar_aire": 2, "localizar_sensor": 1, None: 1}


def test_reset_vacia_tambien_los_desgloses():
    log_decision(EventoDecision(decision=_decision(0), latencia_ms=1.0))
    reset()
    assert desglose_por_nivel() == {}
    assert desglose_por_intencion() == {}


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
    assert registro.candidato_descartado is None
    assert registro.confianza == 0.9
    assert registro.entidades == {"region": "pance"}
    assert registro.entidades_default == ()
    assert registro.latencia_ms == 42.5


def test_log_decision_registra_entidades_default(caplog):
    decision_con_default = Decision(
        intencion="consultar_tendencia_calidad_aire",
        nivel=1,
        confianza=0.8,
        accion=("show_trend",),
        sensitive=False,
        entidades={"periodo": ["24h"]},
        entidades_default=("periodo",),
    )
    with caplog.at_level(logging.INFO, logger="intent_router.metrics"):
        log_decision(EventoDecision(decision=decision_con_default, latencia_ms=5.0))

    registro = caplog.records[0]
    assert registro.entidades_default == ("periodo",)


def test_log_decision_registra_candidato_descartado_en_escalada(caplog):
    decision_escalada = Decision(
        intencion=None,
        nivel=2,
        confianza=0.85,
        accion=("escalate_to_llm",),
        sensitive=True,
        motivos_escalada=("fail_safe_sensitive_en_nivel1",),
        candidato_descartado="activar_alerta",
    )
    with caplog.at_level(logging.INFO, logger="intent_router.metrics"):
        log_decision(EventoDecision(decision=decision_escalada, latencia_ms=10.0))

    registro = caplog.records[0]
    assert registro.intencion is None
    assert registro.candidato_descartado == "activar_alerta"
