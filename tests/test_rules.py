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
    assert resultado.clausulas[0].verbo == "querer"


def test_prioriza_por_orden_no_por_tipo_de_match():
    # "cancelaar" (typo, requiere fallback) aparece antes que "alerta"
    # (match exacto via variante). Gana el primer token resoluble en la
    # frase, no el primer match exacto sin importar la posicion.
    resultado = analizar("Cancelaar la alerta")
    assert resultado.clausulas[0].verbo == "cancelar"


def test_clausula_sin_ningun_verbo_reconocido_da_none():
    resultado = analizar("El clima de Cali hoy")
    assert resultado.clausulas[0].verbo is None


def test_falso_positivo_conocido_sustantivo_con_forma_de_verbo():
    # "alerta" es tambien un sustantivo comun (verb_variants.py lo documenta),
    # asi que un mensaje sin verbo real puede corregirse igual via el
    # fallback de typos: senal barata, no una confirmacion.
    resultado = analizar("La alerta de hoy")
    assert resultado.clausulas[0].verbo == "alertar"
