from intent_router.splitter import dividir_por_conectores
from intent_router.tripwire import detectar_senales


def test_sin_conector_devuelve_una_sola_clausula():
    assert dividir_por_conectores("dame el reporte de hoy") == ["dame el reporte de hoy"]


def test_un_conector_divide_en_dos():
    assert dividir_por_conectores("dame el reporte y activa la alerta") == [
        "dame el reporte",
        "activa la alerta",
    ]


def test_dos_conectores_distintos_dividen_en_dos_clausulas():
    resultado = dividir_por_conectores("dame el reporte pero tambien activa la alerta")
    assert resultado == ["dame el reporte", "activa la alerta"]


def test_tres_conectores_dividen_en_cuatro_clausulas():
    resultado = dividir_por_conectores(
        "dame el reporte y activa la alerta pero revisa el sensor tambien manda el resumen"
    )
    assert resultado == [
        "dame el reporte",
        "activa la alerta",
        "revisa el sensor",
        "manda el resumen",
    ]


def test_conector_al_borde_no_deja_clausula_vacia():
    assert dividir_por_conectores("y dame el reporte") == ["dame el reporte"]
    assert dividir_por_conectores("dame el reporte y") == ["dame el reporte"]


def test_conectores_consecutivos_no_dejan_clausula_vacia():
    assert dividir_por_conectores("dame el reporte y pero activa la alerta") == [
        "dame el reporte",
        "activa la alerta",
    ]


def test_no_confunde_substring_con_token():
    resultado = dividir_por_conectores("quiero ir al aeropuerto y a la playa")
    assert resultado == ["quiero ir al aeropuerto", "a la playa"]


def test_string_vacio_devuelve_lista_vacia():
    assert dividir_por_conectores("") == []


def test_solo_espacios_devuelve_lista_vacia():
    assert dividir_por_conectores("   ") == []


def test_conector_subordinante_no_divide():
    texto = "reviso el sensor mientras esperas el reporte"
    assert dividir_por_conectores(texto) == [texto]


def test_integracion_con_tripwire():
    texto = "dame el reporte y activa la alerta"
    senal = detectar_senales(texto)
    assert senal.tiene_conector is True
    assert len(dividir_por_conectores(texto)) > 1
