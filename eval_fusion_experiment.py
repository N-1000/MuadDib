import json
from pathlib import Path
import numpy as np
import yaml
from sentence_transformers import SentenceTransformer
from intent_router.normalizer import normalize
from eval_corpus_baseline import CORPUS_67, CANONICAL_PATH, MODEL_NAME

BASELINE_JSON = Path(__file__).resolve().parent / "baseline_results.json"
FUSION_RESULTS_JSON = Path(__file__).resolve().parent / "fusion_results.json"


def cargar_canonical_fusionado(ruta: Path) -> dict[str, list[str]]:
    with open(ruta, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    intents = {}
    
    frases_consultar = []
    for item in data.get("intents", []):
        name = item["name"]
        phrases = [normalize(p) for p in item.get("phrases", [])]
        if name in ("consultar_calidad_aire", "comparar_calidad_aire", "consultar_pronostico"):
            frases_consultar.extend(phrases)
        else:
            intents[name] = phrases
            
    intents["consultar_calidad_aire"] = frases_consultar
    return intents


def evaluar_fusion():
    print(f"Cargando baseline previo desde: {BASELINE_JSON}")
    with open(BASELINE_JSON, "r", encoding="utf-8") as f:
        baseline_data = json.load(f)
    baseline_map = {item["mensaje"]: item for item in baseline_data}

    print(f"Cargando canonical fusionado desde: {CANONICAL_PATH}...")
    canonical_fusion = cargar_canonical_fusionado(CANONICAL_PATH)
    print(f"Intenciones resultantes tras fusion: {len(canonical_fusion)}")
    print(f"Total frases en consultar_calidad_aire fusionado: {len(canonical_fusion['consultar_calidad_aire'])}")

    print(f"Cargando modelo de embeddings: {MODEL_NAME}...")
    model = SentenceTransformer(MODEL_NAME)

    # Pre-codificar canonical fusionado
    canonical_index = []
    canonical_phrases = []
    for intent, phrases in canonical_fusion.items():
        for p in phrases:
            canonical_index.append((intent, p))
            canonical_phrases.append(p)

    canonical_vectors = model.encode(canonical_phrases, normalize_embeddings=True, show_progress_bar=False)
    canonical_vectors = np.array(canonical_vectors)

    # Preparar corpus con etiqueta esperada actualizada para los fusionados
    corpus_actualizado = []
    for item in CORPUS_67:
        it = dict(item)
        if it["esperado"] in ("comparar_calidad_aire", "consultar_pronostico"):
            it["esperado"] = "consultar_calidad_aire"
        corpus_actualizado.append(it)

    corpus_mensajes_norm = [normalize(item["mensaje"]) for item in corpus_actualizado]
    corpus_vectors = model.encode(corpus_mensajes_norm, normalize_embeddings=True, show_progress_bar=False)
    corpus_vectors = np.array(corpus_vectors)

    resultados = []
    for i, item in enumerate(corpus_actualizado):
        mensaje_raw = item["mensaje"]
        mensaje_norm = corpus_mensajes_norm[i]
        vec_msg = corpus_vectors[i]
        bloque = item["bloque"]
        esperado = item["esperado"]

        sims_por_intent = {}
        for intent, phrases in canonical_fusion.items():
            matching_indices = [
                idx for idx, (it, p) in enumerate(canonical_index)
                if it == intent and p != mensaje_norm
            ]
            if not matching_indices:
                matching_indices = [idx for idx, (it, _) in enumerate(canonical_index) if it == intent]

            c_intent = np.mean(canonical_vectors[matching_indices], axis=0)
            c_intent = c_intent / np.linalg.norm(c_intent)
            sim = float(np.dot(vec_msg, c_intent))
            sims_por_intent[intent] = sim

        sorted_intents = sorted(sims_por_intent.items(), key=lambda x: x[1], reverse=True)
        top1_intent, s1 = sorted_intents[0]
        top2_intent, s2 = sorted_intents[1]
        delta = s1 - s2

        acierto = None
        if bloque == "core":
            acierto = (top1_intent == esperado)
        elif bloque == "sintagma":
            acierto = (top1_intent == esperado) if esperado else False

        b_item = baseline_map[mensaje_raw]
        resultados.append({
            "indice": i + 1,
            "mensaje": mensaje_raw,
            "bloque": bloque,
            "esperado": esperado,
            "top1_intent": top1_intent,
            "s1": round(s1, 4),
            "top2_intent": top2_intent,
            "s2": round(s2, 4),
            "delta": round(delta, 4),
            "acierto": acierto,
            "acierto_previo": b_item["acierto"],
            "top1_previo": b_item["top1_intent"],
            "s1_previo": b_item["s1"],
            "delta_previo": b_item["delta"],
        })

    return resultados


def analizar_resultados(resultados: list[dict]):
    core = [r for r in resultados if r["bloque"] == "core"]
    aciertos_ahora = sum(1 for r in core if r["acierto"])
    aciertos_antes = sum(1 for r in core if r["acierto_previo"])

    regresiones = [r for r in core if r["acierto_previo"] and not r["acierto"]]
    ganancias = [r for r in core if not r["acierto_previo"] and r["acierto"]]
    siguen_mal = [r for r in core if not r["acierto_previo"] and not r["acierto"]]

    s1_ahora = [r["s1"] for r in core]
    s1_antes = [r["s1_previo"] for r in core]
    delta_ahora = [r["delta"] for r in core]
    delta_antes = [r["delta_previo"] for r in core]

    print("=" * 115)
    print("RESULTADOS DEL EXPERIMENTO DE FUSION: consultar / comparar / pronostico")
    print("=" * 115)
    print(f"Exactitud previa (Baseline):  {aciertos_antes}/{len(core)} ({aciertos_antes/len(core)*100:.1f}%)")
    print(f"Exactitud nueva  (Fusion):    {aciertos_ahora}/{len(core)} ({aciertos_ahora/len(core)*100:.1f}%)")
    print(f"Diferencia neta de aciertos:  {aciertos_ahora - aciertos_antes:+d}")
    print("-" * 115)

    print(f"\nCRITERIO 1: INVARIANZA DE NO-REGRESION (0 regresiones requeridas):")
    print(f"Total regresiones detectadas: {len(regresiones)}")
    if regresiones:
        print("  [FALLO DE CRITERIO] Se degradaron los siguientes casos que antes acertaban:")
        for r in regresiones:
            print(f"    - '{r['mensaje']}': antes={r['top1_previo']} (OK), ahora={r['top1_intent']} (ERR, s1={r['s1']:.4f}, delta={r['delta']:+.4f})")
    else:
        print("  [EXITO] Ningun mensaje que antes acertaba fue absorbido ni degradado por la fusion.")

    print(f"\nGANANCIAS ({len(ganancias)} casos que pasaron a verde):")
    for r in ganancias:
        print(f"  + '{r['mensaje']}': antes={r['top1_previo']}, ahora={r['top1_intent']} (s1={r['s1']:.4f}, delta={r['delta']:+.4f})")

    print(f"\nCASOS QUE SIGUEN FALLANDO ({len(siguen_mal)} casos):")
    for r in siguen_mal:
        print(f"  * '{r['mensaje']}': esperado={r['esperado']} -> clasificado={r['top1_intent']} (s1={r['s1']:.4f}, delta={r['delta']:+.4f})")

    print("\n" + "-" * 115)
    print("CRITERIO 2: COMPARATIVA DE DISTRIBUCION (s1 y delta en el Core):")
    print(f"Similitud Top-1 (s1):")
    print(f"  - Media:   antes={np.mean(s1_antes):.4f} -> ahora={np.mean(s1_ahora):.4f}")
    print(f"  - Mediana: antes={np.median(s1_antes):.4f} -> ahora={np.median(s1_ahora):.4f}")
    print(f"Margen Delta (s1 - s2):")
    print(f"  - Media:   antes={np.mean(delta_antes):+.4f} -> ahora={np.mean(delta_ahora):+.4f}")
    print(f"  - Mediana: antes={np.median(delta_antes):+.4f} -> ahora={np.median(delta_ahora):+.4f}")
    print(f"  - p10:     antes={np.percentile(delta_antes, 10):+.4f} -> ahora={np.percentile(delta_ahora, 10):+.4f}")


def main():
    resultados = evaluar_fusion()
    analizar_resultados(resultados)
    with open(FUSION_RESULTS_JSON, "w", encoding="utf-8") as f:
        json.dump(resultados, f, ensure_ascii=False, indent=2)
    print(f"\nResultados completos exportados a: {FUSION_RESULTS_JSON}")


if __name__ == "__main__":
    main()
