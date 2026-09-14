import json

from intent_router.rules import analizar

ENTRADAS = [
    {"mensaje": "Mostrame la calidad del aire de hoy", "intencion_esperada": "consultar_calidad_aire", "verbos_esperados": ["mostrar"], "tiene_conector_esperado": False, "tiene_negacion_esperada": False, "gap_conocido": None},
    {"mensaje": "Dame el reporte semanal", "intencion_esperada": "solicitar_reporte", "verbos_esperados": ["dar"], "tiene_conector_esperado": False, "tiene_negacion_esperada": False, "gap_conocido": None},
    {"mensaje": "Activa las alertas de contaminacion", "intencion_esperada": "activar_alerta", "verbos_esperados": ["activar"], "tiene_conector_esperado": False, "tiene_negacion_esperada": False, "gap_conocido": None},
    {"mensaje": "Cancela la notificacion de la tarde", "intencion_esperada": "cancelar_notificacion", "verbos_esperados": ["cancelar"], "tiene_conector_esperado": False, "tiene_negacion_esperada": False, "gap_conocido": None},
    {"mensaje": "Enviame el pdf del mes pasado", "intencion_esperada": "solicitar_reporte", "verbos_esperados": ["enviar"], "tiene_conector_esperado": False, "tiene_negacion_esperada": False, "gap_conocido": None},
    {"mensaje": "Actualiza los datos del sensor", "intencion_esperada": "actualizar_sensor", "verbos_esperados": ["actualizar"], "tiene_conector_esperado": False, "tiene_negacion_esperada": False, "gap_conocido": None},
    {"mensaje": "Configura la alerta para PM2.5", "intencion_esperada": "configurar_alerta", "verbos_esperados": ["configurar"], "tiene_conector_esperado": False, "tiene_negacion_esperada": False, "gap_conocido": None},
    {"mensaje": "Revisa el sensor de Melendez", "intencion_esperada": "revisar_sensor", "verbos_esperados": ["revisar"], "tiene_conector_esperado": False, "tiene_negacion_esperada": False, "gap_conocido": None},
    {"mensaje": "Compara la calidad del aire entre Siloe y Ciudad Jardin", "intencion_esperada": "comparar_calidad_aire", "verbos_esperados": ["comparar"], "tiene_conector_esperado": True, "tiene_negacion_esperada": False, "gap_conocido": None},
    {"mensaje": "Avisame si sube la contaminacion", "intencion_esperada": "configurar_notificacion", "verbos_esperados": ["avisar"], "tiene_conector_esperado": False, "tiene_negacion_esperada": False, "gap_conocido": None},
    {"mensaje": "Notificame cuando el aire este malo", "intencion_esperada": "configurar_notificacion", "verbos_esperados": ["notificar"], "tiene_conector_esperado": False, "tiene_negacion_esperada": False, "gap_conocido": None},
    {"mensaje": "Agrega el sensor nuevo a mi lista", "intencion_esperada": "agregar_sensor", "verbos_esperados": ["agregar"], "tiene_conector_esperado": False, "tiene_negacion_esperada": False, "gap_conocido": None},
    {"mensaje": "Quita la alerta de las mananas", "intencion_esperada": "cancelar_alerta", "verbos_esperados": ["quitar"], "tiene_conector_esperado": False, "tiene_negacion_esperada": False, "gap_conocido": None},
    {"mensaje": "Repeti el ultimo reporte", "intencion_esperada": "solicitar_reporte", "verbos_esperados": ["repetir"], "tiene_conector_esperado": False, "tiene_negacion_esperada": False, "gap_conocido": None},
    {"mensaje": "Confirma el cambio de horario", "intencion_esperada": "confirmar_cambio", "verbos_esperados": ["confirmar"], "tiene_conector_esperado": False, "tiene_negacion_esperada": False, "gap_conocido": None},
    {"mensaje": "Ayudame a entender estos datos", "intencion_esperada": "pedir_ayuda", "verbos_esperados": ["ayudar"], "tiene_conector_esperado": False, "tiene_negacion_esperada": False, "gap_conocido": None},
    {"mensaje": "Explicame que significa el indice AQI", "intencion_esperada": "pedir_explicacion", "verbos_esperados": ["explicar"], "tiene_conector_esperado": False, "tiene_negacion_esperada": False, "gap_conocido": None},
    {"mensaje": "Guiame para configurar mi cuenta", "intencion_esperada": "pedir_ayuda", "verbos_esperados": ["guiar"], "tiene_conector_esperado": False, "tiene_negacion_esperada": False, "gap_conocido": None},
    {"mensaje": "Busca el sensor mas cercano", "intencion_esperada": "buscar_sensor", "verbos_esperados": ["buscar"], "tiene_conector_esperado": False, "tiene_negacion_esperada": False, "gap_conocido": None},
    {"mensaje": "Encontra la estacion de Chipichape", "intencion_esperada": "buscar_sensor", "verbos_esperados": ["encontrar"], "tiene_conector_esperado": False, "tiene_negacion_esperada": False, "gap_conocido": None},
    {"mensaje": "Mostrrame el reporte de hoy", "intencion_esperada": "solicitar_reporte", "verbos_esperados": ["mostrar"], "tiene_conector_esperado": False, "tiene_negacion_esperada": False, "gap_conocido": "typo con ratio 75.0 contra 'mostrar', por debajo de UMBRAL_DEFECTO=90"},
    {"mensaje": "Cancelaa la alerta", "intencion_esperada": "cancelar_alerta", "verbos_esperados": ["cancelar"], "tiene_conector_esperado": False, "tiene_negacion_esperada": False, "gap_conocido": "typo con ratio 87.5 contra 'cancelar', por debajo de UMBRAL_DEFECTO=90"},
    {"mensaje": "Actualisa los datos", "intencion_esperada": "actualizar_sensor", "verbos_esperados": ["actualizar"], "tiene_conector_esperado": False, "tiene_negacion_esperada": False, "gap_conocido": "typo con ratio 84.2 contra 'actualizar', por debajo de UMBRAL_DEFECTO=90"},
    {"mensaje": "Confirurar el sensor", "intencion_esperada": "ambiguo_no_resoluble", "verbos_esperados": [None], "tiene_conector_esperado": False, "tiene_negacion_esperada": False, "gap_conocido": None},
    {"mensaje": "No quiero mas notificaciones", "intencion_esperada": "rechazar_notificaciones", "verbos_esperados": ["querer"], "tiene_conector_esperado": False, "tiene_negacion_esperada": True, "gap_conocido": None},
    {"mensaje": "No quiero el reporte pero mandame la alerta", "intencion_esperada": "rechazar_y_solicitar", "verbos_esperados": ["querer", "mandar"], "tiene_conector_esperado": True, "tiene_negacion_esperada": True, "gap_conocido": None},
    {"mensaje": "No me mandes nada hoy", "intencion_esperada": "rechazar_notificaciones", "verbos_esperados": ["mandar"], "tiene_conector_esperado": False, "tiene_negacion_esperada": True, "gap_conocido": "'mandes' (subjuntivo) no esta en VARIANTES_VERBO; ratio 66.7 contra 'mandar', por debajo del umbral"},
    {"mensaje": "Nunca me avises los fines de semana", "intencion_esperada": "rechazar_notificaciones", "verbos_esperados": ["avisar"], "tiene_conector_esperado": False, "tiene_negacion_esperada": True, "gap_conocido": "'avises' (subjuntivo) no esta en VARIANTES_VERBO; ratio 66.7 contra 'avisar', por debajo del umbral"},
    {"mensaje": "Dame el reporte y activa la alerta", "intencion_esperada": "solicitar_reporte_y_activar_alerta", "verbos_esperados": ["dar", "activar"], "tiene_conector_esperado": True, "tiene_negacion_esperada": False, "gap_conocido": None},
    {"mensaje": "Mostrame el mapa y dime el pronostico", "intencion_esperada": "mostrar_mapa_y_pronostico", "verbos_esperados": ["mostrar", "decir"], "tiene_conector_esperado": True, "tiene_negacion_esperada": False, "gap_conocido": None},
    {"mensaje": "Cancela la alerta pero tambien mandame el resumen", "intencion_esperada": "cancelar_alerta_y_solicitar_resumen", "verbos_esperados": ["cancelar", "mandar"], "tiene_conector_esperado": True, "tiene_negacion_esperada": False, "gap_conocido": None},
    {"mensaje": "Como esta el aire hoy", "intencion_esperada": "consultar_calidad_aire", "verbos_esperados": [None], "tiene_conector_esperado": False, "tiene_negacion_esperada": False, "gap_conocido": None},
    {"mensaje": "Cual es el indice de calidad del aire", "intencion_esperada": "consultar_indice_calidad", "verbos_esperados": [None], "tiene_conector_esperado": False, "tiene_negacion_esperada": False, "gap_conocido": None},
    {"mensaje": "Que contamina mas en Cali", "intencion_esperada": "consultar_fuente_contaminacion", "verbos_esperados": [None], "tiene_conector_esperado": False, "tiene_negacion_esperada": False, "gap_conocido": None},
    {"mensaje": "Cuando va a mejorar el aire", "intencion_esperada": "consultar_prediccion", "verbos_esperados": [None], "tiene_conector_esperado": False, "tiene_negacion_esperada": False, "gap_conocido": None},
    {"mensaje": "Donde esta el sensor mas cercano", "intencion_esperada": "buscar_sensor", "verbos_esperados": [None], "tiene_conector_esperado": False, "tiene_negacion_esperada": False, "gap_conocido": None},
    {"mensaje": "Cuanto pm2.5 hay ahorita", "intencion_esperada": "consultar_valor_puntual", "verbos_esperados": [None], "tiene_conector_esperado": False, "tiene_negacion_esperada": False, "gap_conocido": None},
    {"mensaje": "Por que esta tan contaminado hoy", "intencion_esperada": "consultar_causa_contaminacion", "verbos_esperados": [None], "tiene_conector_esperado": False, "tiene_negacion_esperada": False, "gap_conocido": None},
    {"mensaje": "Quien reporta estos datos", "intencion_esperada": "consultar_fuente_datos", "verbos_esperados": ["reportar"], "tiene_conector_esperado": False, "tiene_negacion_esperada": False, "gap_conocido": None},
    {"mensaje": "Que tan grave esta la contaminacion", "intencion_esperada": "consultar_severidad", "verbos_esperados": [None], "tiene_conector_esperado": False, "tiene_negacion_esperada": False, "gap_conocido": None},
    {"mensaje": "Cual sensor esta fallando", "intencion_esperada": "consultar_estado_sensor", "verbos_esperados": [None], "tiene_conector_esperado": False, "tiene_negacion_esperada": False, "gap_conocido": None},
    {"mensaje": "Hola", "intencion_esperada": "saludo", "verbos_esperados": [None], "tiene_conector_esperado": False, "tiene_negacion_esperada": False, "gap_conocido": None},
    {"mensaje": "Buenas tardes", "intencion_esperada": "saludo", "verbos_esperados": [None], "tiene_conector_esperado": False, "tiene_negacion_esperada": False, "gap_conocido": None},
    {"mensaje": "Gracias", "intencion_esperada": "agradecimiento", "verbos_esperados": [None], "tiene_conector_esperado": False, "tiene_negacion_esperada": False, "gap_conocido": None},
    {"mensaje": "Chao", "intencion_esperada": "despedida", "verbos_esperados": [None], "tiene_conector_esperado": False, "tiene_negacion_esperada": False, "gap_conocido": None},
    {"mensaje": "Como estas", "intencion_esperada": "saludo", "verbos_esperados": [None], "tiene_conector_esperado": False, "tiene_negacion_esperada": False, "gap_conocido": None},
    {"mensaje": "Todo bien por aca", "intencion_esperada": "smalltalk", "verbos_esperados": [None], "tiene_conector_esperado": False, "tiene_negacion_esperada": False, "gap_conocido": None},
    {"mensaje": "Oiga y como esta el aire por mi barrio", "intencion_esperada": "consultar_calidad_aire", "verbos_esperados": [None], "tiene_conector_esperado": True, "tiene_negacion_esperada": False, "gap_conocido": None},
    {"mensaje": "Parce mandame el reporte de una vez", "intencion_esperada": "solicitar_reporte", "verbos_esperados": ["mandar"], "tiene_conector_esperado": False, "tiene_negacion_esperada": False, "gap_conocido": None},
    {"mensaje": "Ve activame la alerta pues", "intencion_esperada": "activar_alerta", "verbos_esperados": ["activar"], "tiene_conector_esperado": False, "tiene_negacion_esperada": False, "gap_conocido": None},
    {"mensaje": "Dele mostrame los datos", "intencion_esperada": "consultar_calidad_aire", "verbos_esperados": ["mostrar"], "tiene_conector_esperado": False, "tiene_negacion_esperada": False, "gap_conocido": None},
    {"mensaje": "Listo cancela todo", "intencion_esperada": "cancelar_todo", "verbos_esperados": ["cancelar"], "tiene_conector_esperado": False, "tiene_negacion_esperada": False, "gap_conocido": None},
    {"mensaje": "El aire de Siloe", "intencion_esperada": "consultar_calidad_aire", "verbos_esperados": [None], "tiene_conector_esperado": False, "tiene_negacion_esperada": False, "gap_conocido": None},
    {"mensaje": "La alerta de hoy", "intencion_esperada": "ambiguo_fragmento", "verbos_esperados": [None], "tiene_conector_esperado": False, "tiene_negacion_esperada": False, "gap_conocido": None},
    {"mensaje": "Sensor de Melendez", "intencion_esperada": "consultar_sensor", "verbos_esperados": [None], "tiene_conector_esperado": False, "tiene_negacion_esperada": False, "gap_conocido": None},
    {"mensaje": "Reporte semanal", "intencion_esperada": "solicitar_reporte", "verbos_esperados": [None], "tiene_conector_esperado": False, "tiene_negacion_esperada": False, "gap_conocido": None},
    {"mensaje": "Contaminacion en el centro", "intencion_esperada": "consultar_calidad_aire", "verbos_esperados": [None], "tiene_conector_esperado": False, "tiene_negacion_esperada": False, "gap_conocido": None},
    {"mensaje": "Buenas necesito saber como esta el aire en mi zona y si es necesario activar la alerta por favor", "intencion_esperada": "consultar_y_activar_alerta", "verbos_esperados": ["necesitar", "activar"], "tiene_conector_esperado": True, "tiene_negacion_esperada": False, "gap_conocido": None},
    {"mensaje": "Quisiera un reporte completo de la ultima semana con los niveles de pm2.5 y ozono", "intencion_esperada": "solicitar_reporte", "verbos_esperados": ["querer"], "tiene_conector_esperado": True, "tiene_negacion_esperada": False, "gap_conocido": None},
    {"mensaje": "Podrias decirme si hoy es un buen dia para salir a correr", "intencion_esperada": "consultar_recomendacion_actividad", "verbos_esperados": ["poder"], "tiene_conector_esperado": False, "tiene_negacion_esperada": False, "gap_conocido": "'podrias' (condicional de poder) no esta en VARIANTES_VERBO; ratio 66.7 contra 'poder'"},
    {"mensaje": "Mostrame que esta pasando", "intencion_esperada": "consultar_estado_general", "verbos_esperados": ["mostrar"], "tiene_conector_esperado": False, "tiene_negacion_esperada": False, "gap_conocido": None},
    {"mensaje": "Decime el estado del sensor", "intencion_esperada": "consultar_estado_sensor", "verbos_esperados": ["decir"], "tiene_conector_esperado": False, "tiene_negacion_esperada": False, "gap_conocido": None},
    {"mensaje": "Ayudame con esto por favor", "intencion_esperada": "pedir_ayuda", "verbos_esperados": ["ayudar"], "tiene_conector_esperado": False, "tiene_negacion_esperada": False, "gap_conocido": None},
    {"mensaje": "Necesito saber si puedo salir a trotar", "intencion_esperada": "consultar_recomendacion_actividad", "verbos_esperados": ["necesitar"], "tiene_conector_esperado": False, "tiene_negacion_esperada": False, "gap_conocido": None},
    {"mensaje": "Se puede confiar en estos datos", "intencion_esperada": "consultar_confiabilidad_datos", "verbos_esperados": ["poder"], "tiene_conector_esperado": False, "tiene_negacion_esperada": False, "gap_conocido": "'puede' (3ra persona presente de poder) no esta en VARIANTES_VERBO, solo 'puedo'/'podes'; ratio 60.0 contra 'poder'"},
    {"mensaje": "Hay algun problema con la estacion del sur", "intencion_esperada": "reportar_problema", "verbos_esperados": [None], "tiene_conector_esperado": False, "tiene_negacion_esperada": False, "gap_conocido": None},
    {"mensaje": "Esta funcionando bien todo", "intencion_esperada": "consultar_estado_general", "verbos_esperados": [None], "tiene_conector_esperado": False, "tiene_negacion_esperada": False, "gap_conocido": None},
]


def main() -> None:
    errores = []
    for i, entrada in enumerate(ENTRADAS):
        resultado = analizar(entrada["mensaje"])
        verbos_reales = [c.verbo for c in resultado.clausulas]
        if entrada["gap_conocido"] is None:
            if verbos_reales != entrada["verbos_esperados"]:
                errores.append((i, entrada["mensaje"], "verbos", entrada["verbos_esperados"], verbos_reales))
            if resultado.senales.tiene_conector != entrada["tiene_conector_esperado"]:
                errores.append((i, entrada["mensaje"], "conector", entrada["tiene_conector_esperado"], resultado.senales.tiene_conector))
            if resultado.senales.tiene_negacion != entrada["tiene_negacion_esperada"]:
                errores.append((i, entrada["mensaje"], "negacion", entrada["tiene_negacion_esperada"], resultado.senales.tiene_negacion))
        else:
            if verbos_reales == entrada["verbos_esperados"]:
                errores.append((i, entrada["mensaje"], "gap_ya_no_reproduce", entrada["verbos_esperados"], verbos_reales))

    if errores:
        print(f"{len(errores)} INCONSISTENCIAS entre la etiqueta y el comportamiento real:")
        for e in errores:
            print(" ", e)
        raise SystemExit(1)

    print(f"{len(ENTRADAS)} entradas validadas contra analizar() real. Sin inconsistencias.")
    with open("golden_dataset.json", "w", encoding="utf-8") as f:
        json.dump(ENTRADAS, f, ensure_ascii=False, indent=2)
    print("golden_dataset.json escrito.")


if __name__ == "__main__":
    main()
