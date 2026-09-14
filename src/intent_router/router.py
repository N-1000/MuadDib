from dataclasses import dataclass, field
from typing import Any
from intent_router.embeddings import (
    CanonicalEmbeddings,
    encode,
    esta_disponible,
    precompute_canonical,
    rank_intents,
)
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


@dataclass(frozen=True)
class RoutingResult:
    mensaje: str
    decisiones: tuple[Decision, ...]

    @property
    def es_multi_intencion(self) -> bool:
        """Indica si el mensaje contiene multiples clausulas enrutadas independientemente."""
        return len(self.decisiones) > 1


def _evaluar_nivel0(
    texto_clausula: str,
    negada: bool,
    config_nivel0: dict[str, Any],
) -> Decision | None:
    """Evalua si una clausula cumple alguna regla determinista declarada en Nivel 0."""
    texto_norm = normalize(texto_clausula)
    intents = config_nivel0.get("intents", [])

    for intent in intents:
        nombre = intent["name"]
        modo_match = intent.get("match", "any")
        phrases = [normalize(p) for p in intent.get("phrases", [])]
        sensitive = bool(intent.get("sensitive", False))
        accion = tuple(intent.get("action", []))

        if modo_match == "exact":
            if texto_norm in phrases:
                return Decision(
                    intencion=nombre,
                    nivel=0,
                    confianza=1.0,
                    accion=accion,
                    sensitive=sensitive,
                    negada=negada,
                    clausula=texto_clausula,
                )
        elif modo_match == "all":
            if phrases and all(p in texto_norm for p in phrases):
                return Decision(
                    intencion=nombre,
                    nivel=0,
                    confianza=1.0,
                    accion=accion,
                    sensitive=sensitive,
                    negada=negada,
                    clausula=texto_clausula,
                )
        else:
            if any(p in texto_norm for p in phrases):
                return Decision(
                    intencion=nombre,
                    nivel=0,
                    confianza=1.0,
                    accion=accion,
                    sensitive=sensitive,
                    negada=negada,
                    clausula=texto_clausula,
                )

    return None


def _evaluar_nivel1(
    texto_clausula: str,
    negada: bool,
    canonical_data: CanonicalEmbeddings | None,
    umbral: float,
    margen_min: float,
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

    top1_name, s1, top1_sensitive, top1_action = ranking[0]
    s2 = ranking[1][1] if len(ranking) > 1 else 0.0
    delta = s1 - s2

    if s1 < umbral:
        motivos.append("confianza_insuficiente")

    if len(ranking) > 1 and delta < margen_min:
        motivos.append("margen_ambiguo")

    if top1_sensitive:
        motivos.append("fail_safe_sensitive_en_nivel1")

    if negada:
        motivos.append("clausula_negada_en_nivel1")

    if motivos:
        return Decision(
            intencion=top1_name,
            nivel=2,
            confianza=s1,
            accion=("escalate_to_llm",),
            sensitive=top1_sensitive,
            negada=negada,
            motivos_escalada=tuple(motivos),
            clausula=texto_clausula,
        )

    return Decision(
        intencion=top1_name,
        nivel=1,
        confianza=s1,
        accion=top1_action,
        sensitive=False,
        negada=False,
        motivos_escalada=(),
        clausula=texto_clausula,
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
        decision_n1 = _evaluar_nivel1(mensaje, False, canonical_data, umbral, margen_min)
        return RoutingResult(mensaje=mensaje, decisiones=(decision_n1,))

    for c in clausulas:
        decision_n0 = _evaluar_nivel0(c.texto, c.negada, config)
        if decision_n0 is not None:
            decisiones.append(decision_n0)
            continue

        decision_n1 = _evaluar_nivel1(c.texto, c.negada, canonical_data, umbral, margen_min)
        decisiones.append(decision_n1)

    return RoutingResult(mensaje=mensaje, decisiones=tuple(decisiones))
