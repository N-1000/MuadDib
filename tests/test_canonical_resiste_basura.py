"""Vigila el margen entre el umbral de routing y el techo de similitud de texto fuera de dominio.

El experimento de un intent 'fuera_de_dominio' (conversacion, no en el repo) midio que el
centroide no separa basura de mensajes legitimos: 'dime el pronostico' puntua mas alto que
la basura mas parecida. No hay compuerta que arregle eso, asi que el sistema sigue dependiendo
de que ningun texto ajeno cruce el umbral de Nivel 1. Este test vigila esa dependencia -- no la
resuelve -- para que un canonical.yaml mas denso no la rompa en silencio.

Margen medido al escribir este test: 0.0274 (umbral 0.60, techo de basura 0.5726 en
'dale pues' contra cancelar_alerta). Se espera que ese margen se achique a medida que
canonical.yaml se densifica -- centroides con mas frases tienden a cubrir mas espacio
semantico, incluido el de texto generico. Si este test falla, la lectura correcta no es
"algo se rompio": es "el margen se agoto y routing.threshold (o las frases del intent que
gano) necesitan recalibrarse". Bajar el umbral sin mirar por que goles nuevos aparecen
en la basura resuelve el sintoma, no la causa.
"""

import pytest
from entry_point_referencia import iniciar
from intent_router.embeddings import encode, rank_intents

TEXTO_FUERA_DE_DOMINIO = (
    "el partido de ayer",
    "tengo hambre",
    "dale pues",
    "que hora es",
    "no puedo dormir",
    "mi carro no prende",
    "vamos a comer algo",
    "estoy cansado",
    "hace frio",
    "prendeme la tele",
    "me duele la cabeza",
    "que pelicula vemos",
    "cual es la capital de francia",
    "estoy aburrido",
    "que dia es hoy",
)


@pytest.fixture(scope="module")
def motor():
    return iniciar()


@pytest.mark.parametrize("texto", TEXTO_FUERA_DE_DOMINIO)
def test_texto_fuera_de_dominio_no_supera_el_umbral(motor, texto):
    umbral = motor.config["routing"]["threshold"]
    vec = encode(texto)
    ranking = rank_intents(vec, motor.canonical_data)
    top1_nombre, top1_score = ranking[0][0], ranking[0][1]
    assert top1_score < umbral, (
        f"'{texto}' supera el umbral contra '{top1_nombre}' ({top1_score:.4f} >= {umbral}). "
        f"Esto no es un bug en el codigo: es el margen entre routing.threshold y el techo de "
        f"basura agotandose (era 0.0274 al escribir este test). Recalibrar routing.threshold "
        f"o revisar por que '{top1_nombre}' se volvio mas atractivo para texto generico, no "
        f"bajar el umbral sin mirar la causa."
    )
