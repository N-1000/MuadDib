"""Vigila el margen entre el umbral de routing y el techo de similitud de texto fuera de dominio.

El experimento de un intent 'fuera_de_dominio' (conversacion, no en el repo) midio que el
centroide no separa basura de mensajes legitimos: 'dime el pronostico' puntua mas alto que
la basura mas parecida. No hay compuerta que arregle eso, asi que el sistema sigue dependiendo
de que ningun texto ajeno cruce el umbral de Nivel 1. Este test vigila esa dependencia -- no la
resuelve -- para que un canonical.yaml mas denso no la rompa en silencio.
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
        f"'{texto}' supera el umbral contra '{top1_nombre}' "
        f"({top1_score:.4f} >= {umbral}): el margen que hoy evita quemar LLM en "
        f"texto ajeno se rompio -- revisar canonical.yaml o routing.threshold"
    )
