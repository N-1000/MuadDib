import numpy as np
import pytest
from intent_router.embeddings import CanonicalEmbeddings
from intent_router.router import (
    DEFAULT_MIN_MARGIN,
    DEFAULT_THRESHOLD,
    Decision,
    RoutingResult,
    _evaluar_nivel1,
    resolve,
)


def _crear_canonical_mock(
    intents: tuple[str, ...],
    scores: list[float],
    sensitive_flags: tuple[bool, ...],
    actions: tuple[tuple[str, ...], ...],
) -> tuple[CanonicalEmbeddings, np.ndarray]:
    """Crea centroides mock donde el dot product con vec_query da exactamente scores."""
    dim = 16
    vec_query = np.zeros(dim, dtype=np.float32)
    vec_query[0] = 1.0

    centroids = []
    for s in scores:
        c = np.zeros(dim, dtype=np.float32)
        c[0] = s
        c[1] = np.sqrt(max(0.0, 1.0 - s * s))
        centroids.append(c)

    canonical = CanonicalEmbeddings(
        intents=intents,
        centroids=np.stack(centroids, axis=0),
        phrase_counts=tuple(1 for _ in intents),
        sensitive_flags=sensitive_flags,
        actions=actions,
    )
    return canonical, vec_query


def test_umbral_confianza_limite_exacto(monkeypatch):
    intents = ("consultar_aire", "pedir_ayuda")
    sensitive = (False, False)
    actions = (("show_air",), ("show_help",))

    # Caso limite inferior: s1 = 0.599 -> Falla por debajo de 0.60
    can_inf, v_inf = _crear_canonical_mock(intents, [0.599, 0.400], sensitive, actions)
    monkeypatch.setattr("intent_router.router.encode", lambda _: v_inf)
    monkeypatch.setattr("intent_router.router.esta_disponible", lambda: True)

    d_inf = _evaluar_nivel1("test", can_inf, umbral=0.60, margen_min=0.05)
    assert d_inf.nivel == 2
    assert "confianza_insuficiente" in d_inf.motivos_escalada
    assert "margen_ambiguo" not in d_inf.motivos_escalada

    # Caso limite superior: s1 = 0.601 -> Pasa el umbral
    can_sup, v_sup = _crear_canonical_mock(intents, [0.601, 0.400], sensitive, actions)
    monkeypatch.setattr("intent_router.router.encode", lambda _: v_sup)

    d_sup = _evaluar_nivel1("test", can_sup, umbral=0.60, margen_min=0.05)
    assert d_sup.nivel == 1
    assert d_sup.intencion == "consultar_aire"
    assert d_sup.motivos_escalada == ()


def test_margen_ambiguedad_limite_exacto(monkeypatch):
    intents = ("consultar_aire", "pedir_ayuda")
    sensitive = (False, False)
    actions = (("show_air",), ("show_help",))

    # Caso limite inferior: delta = 0.700 - 0.651 = 0.049 -> Falla margen
    can_inf, v_inf = _crear_canonical_mock(intents, [0.700, 0.651], sensitive, actions)
    monkeypatch.setattr("intent_router.router.encode", lambda _: v_inf)
    monkeypatch.setattr("intent_router.router.esta_disponible", lambda: True)

    d_inf = _evaluar_nivel1("test", can_inf, umbral=0.60, margen_min=0.05)
    assert d_inf.nivel == 2
    assert "margen_ambiguo" in d_inf.motivos_escalada
    assert "confianza_insuficiente" not in d_inf.motivos_escalada

    # Caso limite superior: delta = 0.700 - 0.649 = 0.051 -> Pasa margen
    can_sup, v_sup = _crear_canonical_mock(intents, [0.700, 0.649], sensitive, actions)
    monkeypatch.setattr("intent_router.router.encode", lambda _: v_sup)

    d_sup = _evaluar_nivel1("test", can_sup, umbral=0.60, margen_min=0.05)
    assert d_sup.nivel == 1
    assert d_sup.intencion == "consultar_aire"
    assert d_sup.motivos_escalada == ()


def test_compuerta_sensitive_true_en_nivel1_escala_siempre(monkeypatch):
    intents = ("activar_alerta", "consultar_aire")
    sensitive = (True, False)
    actions = (("enable_alert",), ("show_air",))

    can, vec = _crear_canonical_mock(intents, [0.950, 0.400], sensitive, actions)
    monkeypatch.setattr("intent_router.router.encode", lambda _: vec)
    monkeypatch.setattr("intent_router.router.esta_disponible", lambda: True)

    d = _evaluar_nivel1("activa la alerta", can, umbral=0.60, margen_min=0.05)
    assert d.nivel == 2
    assert d.intencion == "activar_alerta"
    assert d.sensitive is True
    assert "fail_safe_sensitive_en_nivel1" in d.motivos_escalada


def test_registro_exhaustivo_de_multiples_fallos(monkeypatch):
    intents = ("activar_alerta", "consultar_aire")
    sensitive = (True, False)
    actions = (("enable_alert",), ("show_air",))

    # Falla confianza (0.45 < 0.60), margen (0.45 - 0.44 = 0.01 < 0.05) y es sensitive
    can, vec = _crear_canonical_mock(intents, [0.450, 0.440], sensitive, actions)
    monkeypatch.setattr("intent_router.router.encode", lambda _: vec)
    monkeypatch.setattr("intent_router.router.esta_disponible", lambda: True)

    d = _evaluar_nivel1("mensaje ambiguo", can, umbral=0.60, margen_min=0.05)
    assert d.nivel == 2
    assert "confianza_insuficiente" in d.motivos_escalada
    assert "margen_ambiguo" in d.motivos_escalada
    assert "fail_safe_sensitive_en_nivel1" in d.motivos_escalada
    assert len(d.motivos_escalada) == 3


def test_resolucion_nivel0_exact_match():
    config = {
        "intents": [
            {
                "name": "saludo_cortesia",
                "match": "exact",
                "phrases": ["hola", "buenas tardes"],
                "action": ["reply_greeting"],
                "sensitive": False,
            }
        ]
    }
    res = resolve("Hola", config)
    assert isinstance(res, RoutingResult)
    assert res.es_multi_intencion is False
    assert len(res.decisiones) == 1
    d = res.decisiones[0]
    assert d.nivel == 0
    assert d.intencion == "saludo_cortesia"
    assert d.confianza == 1.0
    assert d.accion == ("reply_greeting",)


def test_multi_intencion_enruta_clausulas_independientes():
    config = {
        "intents": [
            {
                "name": "navegar_mapa",
                "phrases": ["mapa"],
                "action": ["navigate"],
                "sensitive": False,
            },
            {
                "name": "consultar_pronostico",
                "phrases": ["pronostico"],
                "action": ["navigate"],
                "sensitive": False,
            },
        ]
    }
    mensaje = "mostrame el mapa y decime el pronostico"
    res = resolve(mensaje, config)
    assert isinstance(res, RoutingResult)
    assert res.es_multi_intencion is True
    assert len(res.decisiones) == 2

    d1, d2 = res.decisiones
    assert d1.nivel == 0
    assert d1.intencion == "navegar_mapa"
    assert d2.nivel == 0
    assert d2.intencion == "consultar_pronostico"


def test_degradacion_sin_modelo():
    config = {"intents": []}
    res = resolve("consulta cualquiera", config, canonical_data=None)
    assert len(res.decisiones) == 1
    d = res.decisiones[0]
    assert d.nivel == 2
    assert d.accion == ("escalate_to_llm",)
    assert "modelo_no_disponible" in d.motivos_escalada
