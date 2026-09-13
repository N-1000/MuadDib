from intent_router.rules import analizar


def test_negacion_se_ata_a_la_clausula_que_la_contiene():
    r = analizar("no quiero el reporte pero mandame la alerta")
    assert [(c.verbo, c.negada) for c in r.clausulas] == [
        ("querer", True),
        ("mandar", False),
    ]


def test_mensajes_opuestos_no_producen_el_mismo_resultado():
    a = analizar("no quiero el reporte pero mandame la alerta")
    b = analizar("quiero el reporte pero no me mandes la alerta")
    assert a.clausulas != b.clausulas


def test_sustantivo_tras_determinante_no_se_toma_como_verbo():
    # Regresion: "no me mandes la alerta" resolvia verbo=alertar, lo contrario
    # de lo pedido, porque el sustantivo "alerta" es tambien variante verbal.
    r = analizar("no me mandes la alerta")
    (clausula,) = r.clausulas
    assert clausula.verbo is None
    assert clausula.negada is True


def test_imperativo_antes_del_determinante_sigue_resolviendo():
    (clausula,) = analizar("activa la alerta").clausulas
    assert clausula.verbo == "activar"


def test_conector_que_une_objetos_no_divide_en_dos_intenciones():
    # Regresion: "y" coordinando sustantivos partia una sola intencion en dos.
    (clausula,) = analizar("mostrame el mapa y el pronostico").clausulas
    assert clausula.verbo == "mostrar"


def test_dos_acciones_reales_si_dividen():
    r = analizar("mostrame el mapa y dime el pronostico")
    assert [c.verbo for c in r.clausulas] == ["mostrar", "decir"]


def test_conector_temporal_no_divide():
    # "despues" y "mientras" son temporales/subordinantes: el tripwire los
    # marca, pero no coordinan dos acciones independientes.
    (clausula,) = analizar("dame el reporte despues de las 5").clausulas
    assert clausula.verbo == "dar"


def test_coordinacion_sin_ningun_verbo_queda_como_una_sola_clausula():
    (clausula,) = analizar("el aire de siloe y el de pance").clausulas
    assert clausula.verbo is None
