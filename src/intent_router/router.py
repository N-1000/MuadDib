from dataclasses import dataclass, field
from typing import Any
from intent_router.embeddings import (
    CanonicalEmbeddings,
    encode,
    esta_disponible,
    precompute_canonical,
    rank_intents,
)
from intent_router.entities import extract_entities
from intent_router.normalizer import normalize
from intent_router.rules import analizar


@dataclass(frozen=True)
class Decision:
    intencion: str | None
    nivel: int
    confianza: float
    accion: tuple[str, ...]
    sensitive: bool
    negada: bool = False
    motivos_escalada: tuple[str, ...] = field(default_factory=tuple)
    clausula: str = ""
    entidades: dict[str, Any] = field(default_factory=dict)
    candidato_descartado: str | None = None
    entidades_default: tuple[str, ...] = field(default_factory=tuple)
    respuesta_texto: str | None = None
    respuesta_fundamentada: bool = False
    herramientas_llamadas: tuple[str, ...] = field(default_factory=tuple)
    herramientas_fallidas: tuple[str, ...] = field(default_factory=tuple)
    herramienta_pendiente: dict[str, Any] | None = None
    tokens_entrada: int = 0
    tokens_salida: int = 0
    latencia_llm_ms: float = 0.0


@dataclass(frozen=True)
class RoutingResult:
    mensaje: str
    decisiones: tuple[Decision, ...]

    @property
    def es_multi_intencion(self) -> bool:
        """Indica si el mensaje contiene multiples clausulas enrutadas independientemente."""
        return len(self.decisiones) > 1


def _evaluar_entidades(
    texto_clausula: str,
    entity_types: tuple[str, ...],
    cardinalidad: str | None,
    config: dict[str, Any],
) -> tuple[dict[str, list[str]], bool]:
    """Extrae entidades y evalua si cumplen la cardinalidad que declara la intencion."""
    entidades = extract_entities(texto_clausula, config)
    if cardinalidad == "multiple":
        cumple = all(len(entidades.get(tipo, [])) >= 2 for tipo in entity_types)
        return entidades, cumple
    return entidades, True


def _aplicar_defaults_entidades(
    entidades: dict[str, list[str]],
    entity_types: tuple[str, ...],
    defaults: dict[str, str],
) -> tuple[dict[str, list[str]], tuple[str, ...]]:
    """Rellena con el default declarado los tipos de entidad que la intencion necesita y el mensaje no proveyo."""
    resultado = dict(entidades)
    aplicados: list[str] = []
    for tipo in entity_types:
        if not resultado.get(tipo) and tipo in defaults:
            resultado[tipo] = [defaults[tipo]]
            aplicados.append(tipo)
    return resultado, tuple(aplicados)


def _evaluar_nivel0(
    texto_clausula: str,
    negada: bool,
    config_nivel0: dict[str, Any],
) -> Decision | None:
    """Evalua si una clausula cumple alguna regla determinista declarada en Nivel 0."""
    texto_norm = normalize(texto_clausula)
    intents = config_nivel0.get("intents", [])

    for intent in intents:
        if _matchea_intent_nivel0(intent, texto_norm):
            return _construir_decision_nivel0(intent, negada, texto_clausula, config_nivel0)

    return None


def _matchea_intent_nivel0(intent: dict[str, Any], texto_norm: str) -> bool:
    """Evalua si texto_norm coincide exactamente con alguna phrase declarada."""
    phrases = [normalize(p) for p in intent.get("phrases", [])]
    return texto_norm in phrases


def _construir_decision_nivel0(
    intent: dict[str, Any],
    negada: bool,
    texto_clausula: str,
    config: dict[str, Any],
) -> Decision:
    """Construye la Decision de Nivel 0; escala a Nivel 2 si la clausula viene negada o le falta cardinalidad de entidad."""
    nombre = intent["name"]
    sensitive = bool(intent.get("sensitive", False))

    if negada:
        return Decision(
            intencion=None,
            nivel=2,
            confianza=1.0,
            accion=("escalate_to_llm",),
            sensitive=sensitive,
            negada=True,
            motivos_escalada=("clausula_negada_en_nivel0",),
            clausula=texto_clausula,
            candidato_descartado=nombre,
        )

    entity_types = tuple(intent.get("entity", []))
    entidades, cardinalidad_ok = _evaluar_entidades(
        texto_clausula,
        entity_types,
        intent.get("entity_cardinality"),
        config,
    )
    if not cardinalidad_ok:
        return Decision(
            intencion=None,
            nivel=2,
            confianza=1.0,
            accion=("escalate_to_llm",),
            sensitive=sensitive,
            negada=False,
            motivos_escalada=("cardinalidad_entidad_insuficiente_en_nivel0",),
            clausula=texto_clausula,
            entidades=entidades,
            candidato_descartado=nombre,
        )

    entidades, defaults_aplicados = _aplicar_defaults_entidades(
        entidades, entity_types, config.get("entity_defaults", {})
    )
    return Decision(
        intencion=nombre,
        nivel=0,
        confianza=1.0,
        accion=tuple(intent.get("action", [])),
        sensitive=sensitive,
        negada=False,
        clausula=texto_clausula,
        entidades=entidades,
        entidades_default=defaults_aplicados,
    )


def _evaluar_nivel1(
    texto_clausula: str,
    negada: bool,
    canonical_data: CanonicalEmbeddings | None,
    umbral: float,
    margen_min: float,
    config: dict[str, Any],
) -> Decision:
    """Evalua una clausula contra centroides de Nivel 1 registrando compuertas auditables."""
    motivos: list[str] = []

    if not esta_disponible() or canonical_data is None:
        motivos.append("modelo_no_disponible")
        return Decision(
            intencion=None,
            nivel=2,
            confianza=0.0,
            accion=("escalate_to_llm",),
            sensitive=False,
            negada=negada,
            motivos_escalada=tuple(motivos),
            clausula=texto_clausula,
        )

    vec_msg = encode(texto_clausula)
    ranking = rank_intents(vec_msg, canonical_data)

    if not ranking:
        motivos.append("sin_candidatos_canonicos")
        return Decision(
            intencion=None,
            nivel=2,
            confianza=0.0,
            accion=("escalate_to_llm",),
            sensitive=False,
            negada=negada,
            motivos_escalada=tuple(motivos),
            clausula=texto_clausula,
        )

    top1_name, s1, top1_sensitive, top1_action, top1_entity_types, top1_cardinalidad = ranking[0]
    s2 = ranking[1][1] if len(ranking) > 1 else 0.0
    delta = s1 - s2

    entidades, cardinalidad_ok = _evaluar_entidades(texto_clausula, top1_entity_types, top1_cardinalidad, config)

    if s1 < umbral:
        motivos.append("confianza_insuficiente")

    if len(ranking) > 1 and delta < margen_min:
        motivos.append("margen_ambiguo")

    if top1_sensitive and top1_action:
        motivos.append("fail_safe_sensitive_en_nivel1")

    if negada:
        motivos.append("clausula_negada_en_nivel1")

    if not cardinalidad_ok:
        motivos.append("cardinalidad_entidad_insuficiente_en_nivel1")

    if motivos:
        return Decision(
            intencion=None,
            nivel=2,
            confianza=s1,
            accion=("escalate_to_llm",),
            sensitive=top1_sensitive,
            negada=negada,
            motivos_escalada=tuple(motivos),
            clausula=texto_clausula,
            entidades=entidades,
            candidato_descartado=top1_name,
        )

    entidades, defaults_aplicados = _aplicar_defaults_entidades(
        entidades, top1_entity_types, config.get("entity_defaults", {})
    )
    return Decision(
        intencion=top1_name,
        nivel=1,
        confianza=s1,
        accion=top1_action,
        sensitive=top1_sensitive,
        negada=False,
        motivos_escalada=(),
        clausula=texto_clausula,
        entidades=entidades,
        entidades_default=defaults_aplicados,
    )


def resolve(
    mensaje: str,
    config: dict[str, Any],
    canonical_data: CanonicalEmbeddings | None = None,
) -> RoutingResult:
    """Orquesta la cascada de enrutamiento 0 -> 1 -> 2 para cada clausula del mensaje."""
    routing_cfg = config["routing"]
    umbral = float(routing_cfg["threshold"])
    margen_min = float(routing_cfg["min_margin"])

    analisis = analizar(mensaje)
    clausulas = analisis.clausulas if analisis.clausulas else ()

    decisiones: list[Decision] = []

    if not clausulas:
        decision_n0 = _evaluar_nivel0(mensaje, False, config)
        if decision_n0 is not None:
            return RoutingResult(mensaje=mensaje, decisiones=(decision_n0,))
        decision_n1 = _evaluar_nivel1(mensaje, False, canonical_data, umbral, margen_min, config)
        return RoutingResult(mensaje=mensaje, decisiones=(decision_n1,))

    for c in clausulas:
        decision_n0 = _evaluar_nivel0(c.texto, c.negada, config)
        if decision_n0 is not None:
            decisiones.append(decision_n0)
            continue

        decision_n1 = _evaluar_nivel1(c.texto, c.negada, canonical_data, umbral, margen_min, config)
        decisiones.append(decision_n1)

    return RoutingResult(mensaje=mensaje, decisiones=tuple(decisiones))
