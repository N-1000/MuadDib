import numpy as np
import pytest
from intent_router.embeddings import (
    CanonicalEmbeddings,
    encode,
    esta_disponible,
    load_model,
    precompute_canonical,
    rank_intents,
)


@pytest.fixture(scope="module")
def modelo_cargado():
    modelo = load_model()
    assert modelo is not None, "El modelo debe cargar exitosamente en local."
    return modelo


def test_load_model_singleton(modelo_cargado):
    m1 = load_model()
    m2 = load_model()
    assert m1 is m2
    assert esta_disponible() is True


def test_encode_vector_unitario(modelo_cargado):
    vec = encode("como esta el aire hoy", modelo=modelo_cargado)
    assert isinstance(vec, np.ndarray)
    assert vec.ndim == 1
    assert vec.dtype == np.float32
    norma = float(np.linalg.norm(vec))
    assert pytest.approx(norma, rel=1e-5) == 1.0


def test_precompute_canonical_y_ranking(modelo_cargado):
    config_prueba = {
        "client": "test_client",
        "intents": [
            {
                "name": "consultar_aire",
                "action": ["show_air"],
                "sensitive": False,
                "phrases": [
                    "como esta el aire hoy",
                    "calidad del aire en cali",
                ],
            },
            {
                "name": "cancelar_servicio",
                "action": ["cancel_account"],
                "sensitive": True,
                "phrases": [
                    "cancela mi suscripcion ahora",
                    "dar de baja el servicio",
                ],
            },
        ],
    }

    canonical = precompute_canonical(config_prueba, modelo=modelo_cargado)
    assert isinstance(canonical, CanonicalEmbeddings)
    assert canonical.intents == ("consultar_aire", "cancelar_servicio")
    assert canonical.phrase_counts == (2, 2)
    assert canonical.sensitive_flags == (False, True)
    assert canonical.actions == (("show_air",), ("cancel_account",))
    assert canonical.centroids.shape[0] == 2

    for c in canonical.centroids:
        norma = float(np.linalg.norm(c))
        assert pytest.approx(norma, rel=1e-5) == 1.0

    vec_consulta = encode("como esta la contaminacion hoy", modelo=modelo_cargado)
    ranking = rank_intents(vec_consulta, canonical)

    assert len(ranking) == 2
    top1_name, top1_sim, top1_sens, top1_act, top1_ent, top1_card = ranking[0]
    top2_name, top2_sim, top2_sens, top2_act, top2_ent, top2_card = ranking[1]

    assert top1_name == "consultar_aire"
    assert top1_sens is False
    assert top1_act == ("show_air",)
    assert top1_ent == ()
    assert top1_card is None
    assert top1_sim > top2_sim
    assert top2_name == "cancelar_servicio"
    assert top2_sens is True


def test_precompute_canonical_propaga_entity_cardinality(modelo_cargado):
    config_prueba = {
        "intents": [
            {
                "name": "comparar_calidad_aire",
                "action": ["compare_zones"],
                "entity": ["region"],
                "entity_cardinality": "multiple",
                "sensitive": False,
                "phrases": ["compara el aire entre siloe y pance"],
            },
            {
                "name": "consultar_calidad_aire",
                "action": ["show_air_quality"],
                "sensitive": False,
                "phrases": ["como esta el aire hoy"],
            },
        ],
    }
    canonical = precompute_canonical(config_prueba, modelo=modelo_cargado)
    assert canonical.entity_types == (("region",), ())
    assert canonical.entity_cardinality == ("multiple", None)


def test_precompute_canonical_sin_intents_levanta_error(modelo_cargado):
    with pytest.raises(ValueError, match="intents"):
        precompute_canonical({"client": "test"}, modelo=modelo_cargado)


def test_encode_sin_modelo_levanta_runtime_error(monkeypatch):
    monkeypatch.setattr("intent_router.embeddings._MODELO_GLOBAL", None)
    with pytest.raises(RuntimeError, match="no esta disponible"):
        encode("hola", modelo=None)
