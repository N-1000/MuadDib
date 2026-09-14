import logging
from dataclasses import dataclass
from typing import Any
import numpy as np
from sentence_transformers import SentenceTransformer
from intent_router.normalizer import normalize

logger = logging.getLogger(__name__)

MODEL_DEFAULT = "paraphrase-multilingual-MiniLM-L12-v2"


@dataclass(frozen=True)
class CanonicalEmbeddings:
    intents: tuple[str, ...]
    centroids: np.ndarray
    phrase_counts: tuple[int, ...]
    sensitive_flags: tuple[bool, ...]
    actions: tuple[tuple[str, ...], ...]
    entity_types: tuple[tuple[str, ...], ...]
    entity_cardinality: tuple[str | None, ...]


_MODELO_GLOBAL: SentenceTransformer | None = None
_FALLA_DE_CARGA: Exception | None = None


def load_model(nombre_modelo: str = MODEL_DEFAULT) -> SentenceTransformer | None:
    """Carga y almacena el modelo singleton de embeddings o registra degradacion."""
    global _MODELO_GLOBAL, _FALLA_DE_CARGA
    if _MODELO_GLOBAL is not None:
        return _MODELO_GLOBAL
    if _FALLA_DE_CARGA is not None:
        return None
    try:
        _MODELO_GLOBAL = SentenceTransformer(nombre_modelo)
        return _MODELO_GLOBAL
    except Exception as exc:
        _FALLA_DE_CARGA = exc
        logger.warning("Fallo al cargar modelo de embeddings '%s': %s", nombre_modelo, exc)
        return None


def esta_disponible() -> bool:
    """Indica si el modelo de embeddings se encuentra listo para operar."""
    return _MODELO_GLOBAL is not None


def encode(texto: str, modelo: SentenceTransformer | None = None) -> np.ndarray:
    """Codifica un texto a vector unitario L2 usando el modelo cargado."""
    m = modelo or _MODELO_GLOBAL
    if m is None:
        raise RuntimeError("El modelo de embeddings no esta disponible o no fue cargado.")
    texto_norm = normalize(texto)
    vec = m.encode([texto_norm], normalize_embeddings=True, show_progress_bar=False)[0]
    return np.asarray(vec, dtype=np.float32)


def precompute_canonical(
    config: dict[str, Any],
    modelo: SentenceTransformer | None = None,
) -> CanonicalEmbeddings:
    """Precalcula centroides unitarios L2 a partir de la configuracion declarativa."""
    m = modelo or _MODELO_GLOBAL
    if m is None:
        raise RuntimeError("No se puede precomputar canonical: modelo no cargado.")

    intents_data = config.get("intents", [])
    if not intents_data:
        raise ValueError("La configuracion no contiene la clave 'intents' o esta vacia.")

    nombres: list[str] = []
    centroides_list: list[np.ndarray] = []
    conteo_frases: list[int] = []
    sensibles: list[bool] = []
    acciones: list[tuple[str, ...]] = []
    tipos_entidad: list[tuple[str, ...]] = []
    cardinalidades: list[str | None] = []

    for item in intents_data:
        nombre = item["name"]
        frases = item.get("phrases", [])
        if not frases:
            continue
        frases_norm = [normalize(f) for f in frases]
        vectores = m.encode(frases_norm, normalize_embeddings=True, show_progress_bar=False)
        centroide = np.mean(vectores, axis=0)
        norma = float(np.linalg.norm(centroide))
        centroide_unitario = centroide / norma if norma > 0 else centroide

        nombres.append(nombre)
        centroides_list.append(np.asarray(centroide_unitario, dtype=np.float32))
        conteo_frases.append(len(frases_norm))
        sensibles.append(bool(item.get("sensitive", False)))
        acciones.append(tuple(item.get("action", [])))
        tipos_entidad.append(tuple(item.get("entity", [])))
        cardinalidades.append(item.get("entity_cardinality"))

    return CanonicalEmbeddings(
        intents=tuple(nombres),
        centroids=np.stack(centroides_list, axis=0),
        phrase_counts=tuple(conteo_frases),
        sensitive_flags=tuple(sensibles),
        actions=tuple(acciones),
        entity_types=tuple(tipos_entidad),
        entity_cardinality=tuple(cardinalidades),
    )


def rank_intents(
    vector_mensaje: np.ndarray,
    canonical_data: CanonicalEmbeddings,
) -> list[tuple[str, float, bool, tuple[str, ...], tuple[str, ...], str | None]]:
    """Calcula similitud coseno contra los centroides y retorna ranking descendente."""
    similitudes = np.dot(canonical_data.centroids, vector_mensaje)
    indices_ordenados = np.argsort(-similitudes)
    ranking = []
    for idx in indices_ordenados:
        ranking.append((
            canonical_data.intents[idx],
            float(similitudes[idx]),
            canonical_data.sensitive_flags[idx],
            canonical_data.actions[idx],
            canonical_data.entity_types[idx],
            canonical_data.entity_cardinality[idx],
        ))
    return ranking
