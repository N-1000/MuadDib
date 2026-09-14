import pytest
from entry_point_referencia import iniciar
from intent_router.metrics import _eventos, hit_rate, reset


@pytest.fixture(autouse=True)
def _limpiar_metrics():
    reset()
    yield
    reset()


def test_procesar_mensaje_resuelve_y_registra_en_metrics():
    motor = iniciar()

    res_saludo = motor.procesar_mensaje("Hola")
    assert res_saludo.decisiones[0].nivel == 0

    res_negado = motor.procesar_mensaje("no quiero el reporte")
    assert res_negado.decisiones[0].nivel == 2

    assert hit_rate() == pytest.approx(0.5)


def test_procesar_mensaje_arma_evento_con_latencia_medida():
    motor = iniciar()
    motor.procesar_mensaje("Hola")

    assert len(_eventos) == 1
    assert _eventos[0].latencia_ms > 0.0
