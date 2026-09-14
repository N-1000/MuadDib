import numpy as np
import pytest
from intent_router.config_loader import cargar_config
from intent_router.embeddings import CanonicalEmbeddings
from intent_router.router import (
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


def test_umbral_confianza_limites_exactos(monkeypatch):
    intents = ("consultar_aire", "pedir_ayuda")
    sensitive = (False, False)
    actions = (("show_air",), ("show_help",))

    # 1. Limite inferior estricto: s1 = 0.599 -> Falla por debajo de 0.60
    can_inf, v_inf = _crear_canonical_mock(intents, [0.599, 0.400], sensitive, actions)
    monkeypatch.setattr("intent_router.router.encode", lambda _: v_inf)
    monkeypatch.setattr("intent_router.router.esta_disponible", lambda: True)

    d_inf = _evaluar_nivel1("test", False, can_inf, umbral=0.60, margen_min=0.05)
    assert d_inf.nivel == 2
    assert "confianza_insuficiente" in d_inf.motivos_escalada

    # 2. Borde exacto: s1 = 0.600 -> Pasa (>= 0.60)
    can_borde, v_borde = _crear_canonical_mock(intents, [0.600, 0.400], sensitive, actions)
    monkeypatch.setattr("intent_router.router.encode", lambda _: v_borde)

    d_borde = _evaluar_nivel1("test", False, can_borde, umbral=0.60, margen_min=0.05)
    assert d_borde.nivel == 1
    assert d_borde.intencion == "consultar_aire"
    assert d_borde.motivos_escalada == ()

    # 3. Limite superior: s1 = 0.601 -> Pasa
    can_sup, v_sup = _crear_canonical_mock(intents, [0.601, 0.400], sensitive, actions)
    monkeypatch.setattr("intent_router.router.encode", lambda _: v_sup)

    d_sup = _evaluar_nivel1("test", False, can_sup, umbral=0.60, margen_min=0.05)
    assert d_sup.nivel == 1
    assert d_sup.intencion == "consultar_aire"
    assert d_sup.motivos_escalada == ()


def test_margen_ambiguedad_limites_exactos(monkeypatch):
    intents = ("consultar_aire", "pedir_ayuda")
    sensitive = (False, False)
    actions = (("show_air",), ("show_help",))

    # 1. Limite inferior: delta = 0.700 - 0.651 = 0.049 -> Falla margen
    can_inf, v_inf = _crear_canonical_mock(intents, [0.700, 0.651], sensitive, actions)
    monkeypatch.setattr("intent_router.router.encode", lambda _: v_inf)
    monkeypatch.setattr("intent_router.router.esta_disponible", lambda: True)

    d_inf = _evaluar_nivel1("test", False, can_inf, umbral=0.60, margen_min=0.05)
    assert d_inf.nivel == 2
    assert "margen_ambiguo" in d_inf.motivos_escalada

    # 2. Borde exacto: delta = 0.700 - 0.650 = 0.050 -> Pasa (>= 0.05)
    can_borde, v_borde = _crear_canonical_mock(intents, [0.700, 0.650], sensitive, actions)
    monkeypatch.setattr("intent_router.router.encode", lambda _: v_borde)

    d_borde = _evaluar_nivel1("test", False, can_borde, umbral=0.60, margen_min=0.05)
    assert d_borde.nivel == 1
    assert d_borde.intencion == "consultar_aire"
    assert d_borde.motivos_escalada == ()

    # 3. Limite superior: delta = 0.700 - 0.649 = 0.051 -> Pasa
    can_sup, v_sup = _crear_canonical_mock(intents, [0.700, 0.649], sensitive, actions)
    monkeypatch.setattr("intent_router.router.encode", lambda _: v_sup)

    d_sup = _evaluar_nivel1("test", False, can_sup, umbral=0.60, margen_min=0.05)
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

    d = _evaluar_nivel1("activa la alerta", False, can, umbral=0.60, margen_min=0.05)
    assert d.nivel == 2
    assert d.intencion == "activar_alerta"
    assert d.sensitive is True
    assert "fail_safe_sensitive_en_nivel1" in d.motivos_escalada


def test_clausula_negada_bloqueada_en_nivel1(monkeypatch):
    intents = ("solicitar_reporte", "pedir_ayuda")
    sensitive = (False, False)
    actions = (("generate_report",), ("show_help",))

    can, vec = _crear_canonical_mock(intents, [0.900, 0.400], sensitive, actions)
    monkeypatch.setattr("intent_router.router.encode", lambda _: vec)
    monkeypatch.setattr("intent_router.router.esta_disponible", lambda: True)

    d = _evaluar_nivel1("no quiero el reporte", True, can, umbral=0.60, margen_min=0.05)
    assert d.nivel == 2
    assert d.negada is True
    assert "clausula_negada_en_nivel1" in d.motivos_escalada


def test_registro_exhaustivo_de_multiples_fallos(monkeypatch):
    intents = ("activar_alerta", "consultar_aire")
    sensitive = (True, False)
    actions = (("enable_alert",), ("show_air",))

    can, vec = _crear_canonical_mock(intents, [0.450, 0.440], sensitive, actions)
    monkeypatch.setattr("intent_router.router.encode", lambda _: vec)
    monkeypatch.setattr("intent_router.router.esta_disponible", lambda: True)

    d = _evaluar_nivel1("mensaje ambiguo", True, can, umbral=0.60, margen_min=0.05)
    assert d.nivel == 2
    assert "confianza_insuficiente" in d.motivos_escalada
    assert "margen_ambiguo" in d.motivos_escalada
    assert "fail_safe_sensitive_en_nivel1" in d.motivos_escalada
    assert "clausula_negada_en_nivel1" in d.motivos_escalada
    assert len(d.motivos_escalada) == 4


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
        ],
        "routing": {"threshold": 0.60, "min_margin": 0.05},
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


def test_multi_intencion_heterogenea_nivel0_y_escalada_sensitive(monkeypatch):
    config = {
        "intents": [
            {
                "name": "navegar_mapa",
                "phrases": ["mapa"],
                "action": ["navigate"],
                "sensitive": False,
            },
        ],
        "routing": {"threshold": 0.60, "min_margin": 0.05},
    }
    # Mock canonical con activar_alerta (sensitive: true)
    can, vec = _crear_canonical_mock(
        ("activar_alerta", "pedir_ayuda"),
        [0.850, 0.400],
        (True, False),
        (("enable_alert",), ("show_help",)),
    )
    monkeypatch.setattr("intent_router.router.encode", lambda _: vec)
    monkeypatch.setattr("intent_router.router.esta_disponible", lambda: True)

    mensaje = "mostrame el mapa y activa la alerta"
    res = resolve(mensaje, config, canonical_data=can)
    assert isinstance(res, RoutingResult)
    assert res.es_multi_intencion is True
    assert len(res.decisiones) == 2

    d1, d2 = res.decisiones
    # Clausula 1: Nivel 0 determinista
    assert d1.nivel == 0
    assert d1.intencion == "navegar_mapa"
    assert d1.sensitive is False

    # Clausula 2: Escala a Nivel 2 por fail_safe_sensitive
    assert d2.nivel == 2
    assert d2.intencion == "activar_alerta"
    assert d2.sensitive is True
    assert "fail_safe_sensitive_en_nivel1" in d2.motivos_escalada


def test_degradacion_sin_modelo():
    config = {"intents": [], "routing": {"threshold": 0.60, "min_margin": 0.05}}
    res = resolve("consulta cualquiera", config, canonical_data=None)
    assert len(res.decisiones) == 1
    d = res.decisiones[0]
    assert d.nivel == 2
    assert d.accion == ("escalate_to_llm",)
    assert "modelo_no_disponible" in d.motivos_escalada


def test_resolve_usa_threshold_de_config_yaml_no_el_viejo_default(tmp_path, monkeypatch):
    """Con threshold=0.80 en config.yaml, s1=0.70 debe escalar (con el viejo default 0.60 no escalaba)."""
    config_path = tmp_path / "config.yaml"
    rules_path = tmp_path / "rules_nivel0.yaml"
    config_path.write_text(
        "client: test\nrouting:\n  threshold: 0.80\n  min_margin: 0.05\n",
        encoding="utf-8",
    )
    rules_path.write_text(
        "client: test\nintents:\n"
        "  - name: intent_no_relacionado\n"
        "    phrases: [\"zzz_no_matchea_nunca\"]\n"
        "    action: [\"reply\"]\n"
        "    sensitive: false\n",
        encoding="utf-8",
    )
    config = cargar_config(config_path, rules_path)

    can, vec = _crear_canonical_mock(
        ("consultar_aire",), [0.70], (False,), (("show_air",),)
    )
    monkeypatch.setattr("intent_router.router.encode", lambda _: vec)
    monkeypatch.setattr("intent_router.router.esta_disponible", lambda: True)

    res = resolve("como esta el aire hoy", config, canonical_data=can)
    d = res.decisiones[0]
    assert d.nivel == 2
    assert "confianza_insuficiente" in d.motivos_escalada


def test_resolve_revienta_sin_seccion_routing():
    config = {"intents": []}
    with pytest.raises(KeyError):
        resolve("hola", config, canonical_data=None)
