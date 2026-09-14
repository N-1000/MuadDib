import argparse
import sys
from pathlib import Path
import numpy as np
import yaml
from sentence_transformers import SentenceTransformer
from intent_router.normalizer import normalize

MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"
CANONICAL_PATH = Path(__file__).resolve().parent / "clients" / "ecopulse" / "canonical.yaml"


def cargar_canonical(ruta: Path) -> dict[str, list[str]]:
    with open(ruta, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    intents = {}
    for item in data.get("intents", []):
        name = item["name"]
        phrases = [normalize(p) for p in item.get("phrases", [])]
        intents[name] = phrases
    return intents


def evaluar_leave_one_out(intents: dict[str, list[str]], model: SentenceTransformer):
    all_phrases = []
    phrase_to_intent = []
    for intent, phrases in intents.items():
        for p in phrases:
            all_phrases.append(p)
            phrase_to_intent.append(intent)

    embeddings = model.encode(all_phrases, normalize_embeddings=True, show_progress_bar=False)
    embeddings = np.array(embeddings)

    intent_indices: dict[str, list[int]] = {}
    for idx, intent in enumerate(phrase_to_intent):
        intent_indices.setdefault(intent, []).append(idx)

    resultados = []
    colisiones = 0

    print(f"{'Intencion':<28} | {'Propia':<6} | {'Mejor Otra':<6} | {'Margen':<6} | {'Estado':<8} | Frase")
    print("-" * 100)

    for intent, indices in intent_indices.items():
        if len(indices) < 2:
            raise ValueError(f"Intencion '{intent}' tiene menos de 2 frases; no se puede hacer leave-one-out.")

        for idx in indices:
            frase = all_phrases[idx]
            vec_p = embeddings[idx]

            other_own_indices = [i for i in indices if i != idx]
            centroid_own = np.mean(embeddings[other_own_indices], axis=0)
            centroid_own = centroid_own / np.linalg.norm(centroid_own)
            sim_own = float(np.dot(vec_p, centroid_own))

            best_other_intent = None
            best_other_sim = -1.0

            for other_intent, other_indices in intent_indices.items():
                if other_intent == intent:
                    continue
                c_other = np.mean(embeddings[other_indices], axis=0)
                c_other = c_other / np.linalg.norm(c_other)
                sim_other = float(np.dot(vec_p, c_other))
                if sim_other > best_other_sim:
                    best_other_sim = sim_other
                    best_other_intent = other_intent

            margen = sim_own - best_other_sim
            es_colision = margen <= 0
            if es_colision:
                colisiones += 1
                estado = "COLISION"
            elif margen < 0.10:
                estado = "CERCA"
            else:
                estado = "OK"

            resultados.append({
                "intent": intent,
                "frase": frase,
                "sim_own": sim_own,
                "sim_other": best_other_sim,
                "best_other_intent": best_other_intent,
                "margen": margen,
                "es_colision": es_colision,
            })

            print(f"{intent:<28} | {sim_own:.4f} | {best_other_sim:.4f} | {margen:+.4f} | {estado:<8} | {frase}")

    print("-" * 100)
    total = len(resultados)
    margenes = [r["margen"] for r in resultados]
    sims_own = [r["sim_own"] for r in resultados]
    sims_other = [r["sim_other"] for r in resultados]

    print(f"Total frases evaluadas: {total}")
    print(f"Colisiones (margen <= 0): {colisiones} ({colisiones / total * 100:.1f}%)")
    print(f"Margen promedio: {np.mean(margenes):+.4f} (min: {np.min(margenes):+.4f}, max: {np.max(margenes):+.4f})")
    print(f"Similitud promedio propia: {np.mean(sims_own):.4f}")
    print(f"Similitud promedio mejor otra: {np.mean(sims_other):.4f}")

    if colisiones > 0:
        print("\nDetalle de colisiones:")
        for r in resultados:
            if r["es_colision"]:
                print(f"  - [{r['intent']}] '{r['frase']}' -> mas cerca de [{r['best_other_intent']}] (propia: {r['sim_own']:.4f}, otra: {r['sim_other']:.4f}, margen: {r['margen']:+.4f})")

    zona_cerca = [r for r in resultados if not r["es_colision"] and r["margen"] < 0.10]
    if zona_cerca:
        print(f"\nFrases en zona de riesgo (margen < 0.10, {len(zona_cerca)} casos):")
        for r in zona_cerca:
            print(f"  - [{r['intent']}] '{r['frase']}' vs [{r['best_other_intent']}] (margen: {r['margen']:+.4f})")

    return resultados, colisiones


def main():
    parser = argparse.ArgumentParser(description="Leave-one-out validation de canonical.yaml")
    parser.add_argument("--strict", action="store_true", help="Falla si hay alguna colision")
    args = parser.parse_args()

    print(f"Cargando {CANONICAL_PATH}...")
    intents = cargar_canonical(CANONICAL_PATH)
    total_frases = sum(len(p) for p in intents.values())
    print(f"Intenciones: {len(intents)}, Frases: {total_frases}")

    print(f"Cargando modelo '{MODEL_NAME}'...")
    model = SentenceTransformer(MODEL_NAME)

    _, colisiones = evaluar_leave_one_out(intents, model)
    if args.strict and colisiones > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
