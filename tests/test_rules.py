from intent_router.rules import analizar


def test_mensaje_simple_sin_conector_una_clausula():
    resultado = analizar("Mostrame el reporte de hoy")
    assert resultado.texto_normalizado == "mostrame el reporte de hoy"
    assert resultado.senales.tiene_conector is False
    assert len(resultado.clausulas) == 1
    assert resultado.clausulas[0].texto == "mostrame el reporte de hoy"
    assert resultado.clausulas[0].verbo == "mostrar"


def test_mensaje_con_conector_divide_en_clausulas_con_su_propio_verbo():
    resultado = analizar("Dame el reporte y activa la alerta")
    assert resultado.senales.tiene_conector is True
    assert len(resultado.clausulas) == 2
    assert resultado.clausulas[0].texto == "dame el reporte"
    assert resultado.clausulas[0].verbo == "dar"
    assert resultado.clausulas[1].texto == "activa la alerta"
    assert resultado.clausulas[1].verbo == "activar"


def test_negacion_se_marca_pero_no_se_interpreta():
    resultado = analizar("No quiero el reporte")
    assert resultado.senales.tiene_negacion is True
    assert resultado.clausulas[0].negada is True
    assert resultado.clausulas[0].verbo == "querer"


def test_negacion_es_por_clausula_no_global():
    resultado = analizar("No quiero notificaciones pero mandame el reporte igual")
    assert len(resultado.clausulas) == 2
    assert resultado.clausulas[0].negada is True
    assert resultado.clausulas[1].negada is False


def test_prioriza_por_orden_no_por_tipo_de_match():
    # "cancelaar" (typo, requiere fallback) aparece antes que "alerta"
    # (match exacto via variante). Gana el primer token resoluble en la
    # frase, no el primer match exacto sin importar la posicion.
    resultado = analizar("Cancelaar la alerta")
    assert resultado.clausulas[0].verbo == "cancelar"


def test_clausula_sin_ningun_verbo_reconocido_da_none():
    resultado = analizar("El clima de Cali hoy")
    assert resultado.clausulas[0].verbo is None


def test_sustantivo_tras_determinante_no_se_confunde_con_verbo():
    # "alerta" es tambien un verbo (ver verb_variants.py), pero aca es
    # sustantivo: el token anterior ("la") es un determinante, asi que
    # no se intenta resolver como verbo.
    resultado = analizar("La alerta de hoy")
    assert resultado.clausulas[0].verbo is None


def test_mismo_token_como_verbo_sin_determinante_antes_si_resuelve():
    resultado = analizar("Alerta a los vecinos")
    assert resultado.clausulas[0].verbo == "alertar"


def test_conector_sin_dos_clausulas_con_verbo_no_divide():
    # Si el split no deja al menos dos clausulas con verbo propio, se
    # trata el mensaje completo como una sola clausula en vez de partirlo
    # en fragmentos sin sentido ("buenas tardes" no tiene verbo).
    resultado = analizar("quiero el reporte y buenas tardes")
    assert len(resultado.clausulas) == 1
    assert resultado.clausulas[0].verbo == "querer"
