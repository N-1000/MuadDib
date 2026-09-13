from intent_router.normalizer import normalize
from intent_router.tripwire import SenalTripwire, detectar_senales


def test_mensaje_sin_senales():
    senal = detectar_senales("dame el reporte de hoy")
    assert senal.conectores == frozenset()
    assert senal.negaciones == frozenset()
    assert senal.tiene_conector is False
    assert senal.tiene_negacion is False


def test_detecta_conector():
    senal = detectar_senales("dame el reporte y activa la alerta")
    assert senal.tiene_conector is True
    assert "y" in senal.conectores
    assert senal.tiene_negacion is False


def test_detecta_negacion():
    senal = detectar_senales("no quiero el reporte")
    assert senal.tiene_negacion is True
    assert "no" in senal.negaciones
    assert senal.tiene_conector is False


def test_detecta_conector_y_negacion_juntos():
    senal = detectar_senales("no quiero el reporte pero tambien quiero la alerta")
    assert senal.tiene_conector is True
    assert senal.tiene_negacion is True
    assert senal.conectores == frozenset({"pero", "tambien"})
    assert senal.negaciones == frozenset({"no"})


def test_no_confunde_substring_con_token():
    senal = detectar_senales("quiero notificar esto")
    assert senal.tiene_negacion is False
    assert senal.negaciones == frozenset()


def test_string_vacio_no_rompe():
    senal = detectar_senales("")
    assert senal.tiene_conector is False
    assert senal.tiene_negacion is False


def test_integracion_con_normalize():
    texto = normalize("NO quiero ésto, pero también dame el reporte")
    senal = detectar_senales(texto)
    assert senal.tiene_negacion is True
    assert senal.tiene_conector is True
    assert senal.conectores == frozenset({"pero", "tambien"})


def test_senal_es_inmutable():
    senal = SenalTripwire(conectores=frozenset({"y"}), negaciones=frozenset())
    assert isinstance(senal.conectores, frozenset)
    try:
        senal.conectores = frozenset()  # type: ignore[misc]
        assert False, "no deberia permitir reasignar un campo frozen"
    except AttributeError:
        pass
