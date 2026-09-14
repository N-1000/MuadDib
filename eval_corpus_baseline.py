import json
from pathlib import Path
import numpy as np
import yaml
from sentence_transformers import SentenceTransformer
from intent_router.normalizer import normalize

MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"
CANONICAL_PATH = Path(__file__).resolve().parent / "clients" / "ecopulse" / "canonical.yaml"
OUTPUT_JSON = Path(__file__).resolve().parent / "baseline_results.json"

# Las 67 frases de frases.txt clasificadas en sus 5 bloques arquitectonicos
CORPUS_67 = [
    # Bloque 1: Core monoclausula (46 frases)
    {"mensaje": "Mostrame la calidad del aire de hoy", "bloque": "core", "esperado": "consultar_calidad_aire"},
    {"mensaje": "Dame el reporte semanal", "bloque": "core", "esperado": "solicitar_reporte"},
    {"mensaje": "Activa las alertas de contaminacion", "bloque": "core", "esperado": "activar_alerta"},
    {"mensaje": "Cancela la notificacion de la tarde", "bloque": "core", "esperado": "cancelar_alerta"},
    {"mensaje": "Enviame el pdf del mes pasado", "bloque": "core", "esperado": "solicitar_reporte"},
    {"mensaje": "Actualiza los datos del sensor", "bloque": "core", "esperado": "actualizar_datos_sensor"},
    {"mensaje": "Configura la alerta para PM2.5", "bloque": "core", "esperado": "configurar_alerta"},
    {"mensaje": "Revisa el sensor de Melendez", "bloque": "core", "esperado": "consultar_estado_sensor"},
    {"mensaje": "Compara la calidad del aire entre Siloe y Ciudad Jardin", "bloque": "core", "esperado": "comparar_calidad_aire"},
    {"mensaje": "Avisame si sube la contaminacion", "bloque": "core", "esperado": "activar_alerta"},
    {"mensaje": "Notificame cuando el aire este malo", "bloque": "core", "esperado": "activar_alerta"},
    {"mensaje": "Agrega el sensor nuevo a mi lista", "bloque": "core", "esperado": "agregar_sensor"},
    {"mensaje": "Quita la alerta de las mananas", "bloque": "core", "esperado": "cancelar_alerta"},
    {"mensaje": "Repeti el ultimo reporte", "bloque": "core", "esperado": "solicitar_reporte"},
    {"mensaje": "Ayudame a entender estos datos", "bloque": "core", "esperado": "pedir_ayuda_soporte"},
    {"mensaje": "Explicame que significa el indice AQI", "bloque": "core", "esperado": "pedir_ayuda_soporte"},
    {"mensaje": "Guiame para configurar mi cuenta", "bloque": "core", "esperado": "pedir_ayuda_soporte"},
    {"mensaje": "Busca el sensor mas cercano", "bloque": "core", "esperado": "localizar_sensor"},
    {"mensaje": "Encontra la estacion de Chipichape", "bloque": "core", "esperado": "localizar_sensor"},
    {"mensaje": "No quiero mas notificaciones", "bloque": "core", "esperado": "cancelar_alerta"},
    {"mensaje": "No me mandes nada hoy", "bloque": "core", "esperado": "cancelar_alerta"},
    {"mensaje": "Nunca me avises los fines de semana", "bloque": "core", "esperado": "cancelar_alerta"},
    {"mensaje": "Como esta el aire hoy", "bloque": "core", "esperado": "consultar_calidad_aire"},
    {"mensaje": "Cual es el indice de calidad del aire", "bloque": "core", "esperado": "consultar_calidad_aire"},
    {"mensaje": "Que contamina mas en Cali", "bloque": "core", "esperado": "consultar_calidad_aire"},
    {"mensaje": "Cuando va a mejorar el aire", "bloque": "core", "esperado": "consultar_pronostico"},
    {"mensaje": "Donde esta el sensor mas cercano", "bloque": "core", "esperado": "localizar_sensor"},
    {"mensaje": "Cuanto pm2.5 hay ahorita", "bloque": "core", "esperado": "consultar_calidad_aire"},
    {"mensaje": "Por que esta tan contaminado hoy", "bloque": "core", "esperado": "consultar_calidad_aire"},
    {"mensaje": "Quien reporta estos datos", "bloque": "core", "esperado": "pedir_ayuda_soporte"},
    {"mensaje": "Que tan grave esta la contaminacion", "bloque": "core", "esperado": "consultar_calidad_aire"},
    {"mensaje": "Cual sensor esta fallando", "bloque": "core", "esperado": "consultar_estado_sensor"},
    {"mensaje": "Oiga y como esta el aire por mi barrio", "bloque": "core", "esperado": "consultar_calidad_aire"},
    {"mensaje": "Parce mandame el reporte de una vez", "bloque": "core", "esperado": "solicitar_reporte"},
    {"mensaje": "Ve activame la alerta pues", "bloque": "core", "esperado": "activar_alerta"},
    {"mensaje": "Dele mostrame los datos", "bloque": "core", "esperado": "consultar_calidad_aire"},
    {"mensaje": "Listo cancela todo", "bloque": "core", "esperado": "cancelar_alerta"},
    {"mensaje": "Quisiera un reporte completo de la ultima semana con los niveles de pm2.5 y ozono", "bloque": "core", "esperado": "solicitar_reporte"},
    {"mensaje": "Podrias decirme si hoy es un buen dia para salir a correr", "bloque": "core", "esperado": "recomendar_actividad_salud"},
    {"mensaje": "Mostrame que esta pasando", "bloque": "core", "esperado": "consultar_calidad_aire"},
    {"mensaje": "Decime el estado del sensor", "bloque": "core", "esperado": "consultar_estado_sensor"},
    {"mensaje": "Ayudame con esto por favor", "bloque": "core", "esperado": "pedir_ayuda_soporte"},
    {"mensaje": "Necesito saber si puedo salir a trotar", "bloque": "core", "esperado": "recomendar_actividad_salud"},
    {"mensaje": "Se puede confiar en estos datos", "bloque": "core", "esperado": "pedir_ayuda_soporte"},
    {"mensaje": "Hay algun problema con la estacion del sur", "bloque": "core", "esperado": "consultar_estado_sensor"},
    {"mensaje": "Esta funcionando bien todo", "bloque": "core", "esperado": "consultar_estado_sensor"},

    # Bloque 2: Sintagmas nominales / sin verbo (5 frases)
    {"mensaje": "El aire de Siloe", "bloque": "sintagma", "esperado": "consultar_calidad_aire"},
    {"mensaje": "La alerta de hoy", "bloque": "sintagma", "esperado": None},  # Duda anotada, sin intent
    {"mensaje": "Sensor de Melendez", "bloque": "sintagma", "esperado": "consultar_estado_sensor"},
    {"mensaje": "Reporte semanal", "bloque": "sintagma", "esperado": "solicitar_reporte"},
    {"mensaje": "Contaminacion en el centro", "bloque": "sintagma", "esperado": "consultar_calidad_aire"},

    # Bloque 3: Multi-intencion (5 frases)
    {"mensaje": "No quiero el reporte pero mandame la alerta", "bloque": "multi_intencion", "esperado": ["solicitar_reporte", "activar_alerta"]},
    {"mensaje": "Dame el reporte y activa la alerta", "bloque": "multi_intencion", "esperado": ["solicitar_reporte", "activar_alerta"]},
    {"mensaje": "Mostrame el mapa y dime el pronostico", "bloque": "multi_intencion", "esperado": ["consultar_calidad_aire", "consultar_pronostico"]},
    {"mensaje": "Cancela la alerta pero tambien mandame el resumen", "bloque": "multi_intencion", "esperado": ["cancelar_alerta", "solicitar_reporte"]},
    {"mensaje": "Buenas necesito saber como esta el aire en mi zona y si es necesario activar la alerta por favor", "bloque": "multi_intencion", "esperado": ["consultar_calidad_aire", "activar_alerta"]},

    # Bloque 4: Saludos (6 frases) y Typos (4 frases)
    {"mensaje": "Hola", "bloque": "saludo", "esperado": None},
    {"mensaje": "Buenas tardes", "bloque": "saludo", "esperado": None},
    {"mensaje": "Gracias", "bloque": "saludo", "esperado": None},
    {"mensaje": "Chao", "bloque": "saludo", "esperado": None},
    {"mensaje": "Como estas", "bloque": "saludo", "esperado": None},
    {"mensaje": "Todo bien por aca", "bloque": "saludo", "esperado": None},
    {"mensaje": "Mostrrame el reporte de hoy", "bloque": "typo", "esperado": "solicitar_reporte"},
    {"mensaje": "Cancelaa la alerta", "bloque": "typo", "esperado": "cancelar_alerta"},
    {"mensaje": "Actualisa los datos", "bloque": "typo", "esperado": "actualizar_datos_sensor"},
    {"mensaje": "Confirurar el sensor", "bloque": "typo", "esperado": "consultar_estado_sensor"},

    # Bloque 5: Fuera de dominio (1 frase)
    {"mensaje": "Confirma el cambio de horario", "bloque": "fuera_de_dominio", "esperado": None},
]


def cargar_canonical(ruta: Path) -> dict[str, list[str]]:
    with open(ruta, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    intents = {}
    for item in data.get("intents", []):
        name = item["name"]
        phrases = [normalize(p) for p in item.get("phrases", [])]
        intents[name] = phrases
    return intents


def evaluar_corpus(corpus: list[dict], canonical: dict[str, list[str]], model: SentenceTransformer):
    # Pre-codificar todas las frases canonicas
    canonical_index = []
    canonical_phrases = []
    for intent, phrases in canonical.items():
        for p in phrases:
            canonical_index.append((intent, p))
            canonical_phrases.append(p)

    canonical_vectors = model.encode(canonical_phrases, normalize_embeddings=True, show_progress_bar=False)
    canonical_vectors = np.array(canonical_vectors)

    # Pre-codificar todos los mensajes del corpus
    corpus_mensajes_norm = [normalize(item["mensaje"]) for item in corpus]
    corpus_vectors = model.encode(corpus_mensajes_norm, normalize_embeddings=True, show_progress_bar=False)
    corpus_vectors = np.array(corpus_vectors)

    resultados = []

    for i, item in enumerate(corpus):
        mensaje_raw = item["mensaje"]
        mensaje_norm = corpus_mensajes_norm[i]
        vec_msg = corpus_vectors[i]
        bloque = item["bloque"]
        esperado = item["esperado"]

        sims_por_intent = {}
        for intent, phrases in canonical.items():
            # Filtrar phrase si coincide con mensaje_norm (Leave-one-out)
            matching_indices = [
                idx for idx, (it, p) in enumerate(canonical_index)
                if it == intent and p != mensaje_norm
            ]
            if not matching_indices:
                # Si se vacia la intencion (solo tenia esa frase), usar todas
                matching_indices = [idx for idx, (it, _) in enumerate(canonical_index) if it == intent]

            c_intent = np.mean(canonical_vectors[matching_indices], axis=0)
            c_intent = c_intent / np.linalg.norm(c_intent)
            sim = float(np.dot(vec_msg, c_intent))
            sims_por_intent[intent] = sim

        # Ordenar intenciones por similitud descendente
        sorted_intents = sorted(sims_por_intent.items(), key=lambda x: x[1], reverse=True)
        top1_intent, s1 = sorted_intents[0]
        top2_intent, s2 = sorted_intents[1]
        delta = s1 - s2

        acierto = None
        if bloque == "core":
            acierto = (top1_intent == esperado)
        elif bloque == "sintagma":
            acierto = (top1_intent == esperado) if esperado else False
        elif bloque == "multi_intencion":
            acierto = (top1_intent in esperado)
        elif bloque == "typo":
            acierto = (top1_intent == esperado)

        resultados.append({
            "indice": i + 1,
            "mensaje": mensaje_raw,
            "mensaje_norm": mensaje_norm,
            "bloque": bloque,
            "esperado": esperado,
            "top1_intent": top1_intent,
            "s1": round(s1, 4),
            "top2_intent": top2_intent,
            "s2": round(s2, 4),
            "delta": round(delta, 4),
            "acierto": acierto,
        })

    return resultados


def imprimir_reporte(resultados: list[dict]):
    print("=" * 115)
    print("LINEA BASE: EVALUACION DE LOS 67 MENSAJES (LEAVE-ONE-OUT CONTRA CANONICAL.YAML)")
    print("=" * 115)
    print(f"{'#':<3} | {'Bloque':<15} | {'Esperado':<25} | {'Top 1':<25} | {'s1':<6} | {'s2':<6} | {'Delta':<6} | {'OK?':<5} | Mensaje")
    print("-" * 115)

    for r in resultados:
        ok_str = "SI" if r["acierto"] is True else ("NO" if r["acierto"] is False else "-")
        esp_str = str(r["esperado"]) if r["esperado"] else "-"
        print(f"{r['indice']:<3} | {r['bloque']:<15} | {esp_str[:25]:<25} | {r['top1_intent'][:25]:<25} | {r['s1']:.4f} | {r['s2']:.4f} | {r['delta']:+.4f} | {ok_str:<5} | {r['mensaje']}")

    print("=" * 115)
    print("\nRESUMEN POR BLOQUES:")

    # Core
    core_res = [r for r in resultados if r["bloque"] == "core"]
    core_aciertos = sum(1 for r in core_res if r["acierto"])
    core_s1 = [r["s1"] for r in core_res]
    core_delta = [r["delta"] for r in core_res]
    print(f"\n1. CORE MONOCLAUSULA ({len(core_res)} frases):")
    print(f"   - Exactitud (Top-1 == Esperado): {core_aciertos}/{len(core_res)} ({core_aciertos/len(core_res)*100:.1f}%)")
    print(f"   - Similitud Top-1 (s1): media={np.mean(core_s1):.4f}, mediana={np.median(core_s1):.4f}, p10={np.percentile(core_s1, 10):.4f}, min={np.min(core_s1):.4f}, max={np.max(core_s1):.4f}")
    print(f"   - Margen Delta (s1-s2): media={np.mean(core_delta):+.4f}, mediana={np.median(core_delta):+.4f}, p10={np.percentile(core_delta, 10):+.4f}, min={np.min(core_delta):+.4f}")

    errores_core = [r for r in core_res if not r["acierto"]]
    if errores_core:
        print(f"   - Desaciertos ({len(errores_core)} casos):")
        for e in errores_core:
            print(f"     * '{e['mensaje']}' -> Esperado: {e['esperado']} | Clasificado: {e['top1_intent']} (s1={e['s1']:.4f}, s2={e['s2']:.4f}, delta={e['delta']:+.4f})")

    # Sintagmas
    sint_res = [r for r in resultados if r["bloque"] == "sintagma"]
    print(f"\n2. SINTAGMAS NOMINALES ({len(sint_res)} frases):")
    for r in sint_res:
        print(f"   - '{r['mensaje']}' -> Top1: {r['top1_intent']} (s1={r['s1']:.4f}, s2={r['s2']:.4f}, delta={r['delta']:+.4f})")

    # Multi-intencion
    multi_res = [r for r in resultados if r["bloque"] == "multi_intencion"]
    print(f"\n3. MULTI-INTENCION ({len(multi_res)} frases):")
    for r in multi_res:
        print(f"   - '{r['mensaje']}' -> Inclinacion Top1: {r['top1_intent']} (s1={r['s1']:.4f}, s2={r['s2']:.4f}, delta={r['delta']:+.4f})")

    # Typos
    typo_res = [r for r in resultados if r["bloque"] == "typo"]
    typo_aciertos = sum(1 for r in typo_res if r["acierto"])
    print(f"\n4. TYPOS ({len(typo_res)} frases):")
    print(f"   - Top-1 coincide con intencion subyacente: {typo_aciertos}/{len(typo_res)}")
    for r in typo_res:
        print(f"   - '{r['mensaje']}' -> Top1: {r['top1_intent']} (s1={r['s1']:.4f}, delta={r['delta']:+.4f}) | Subyacente: {r['esperado']}")

    # Saludos
    saludo_res = [r for r in resultados if r["bloque"] == "saludo"]
    saludo_s1 = [r["s1"] for r in saludo_res]
    print(f"\n5. SALUDOS / CORTESIA ({len(saludo_res)} frases - Nivel 0 puro):")
    print(f"   - Similitud maxima capturada por N1: media={np.mean(saludo_s1):.4f}, max={np.max(saludo_s1):.4f}")
    for r in saludo_res:
        print(f"   - '{r['mensaje']}' -> Cae errante en: {r['top1_intent']} (s1={r['s1']:.4f}, delta={r['delta']:+.4f})")

    # Fuera de dominio
    fdd_res = [r for r in resultados if r["bloque"] == "fuera_de_dominio"]
    print(f"\n6. FUERA DE DOMINIO ({len(fdd_res)} frases):")
    for r in fdd_res:
        print(f"   - '{r['mensaje']}' -> Asignado a: {r['top1_intent']} (s1={r['s1']:.4f}, delta={r['delta']:+.4f})")


def main():
    print(f"Cargando canonical desde: {CANONICAL_PATH}")
    canonical = cargar_canonical(CANONICAL_PATH)
    print(f"Cargando modelo de embeddings: {MODEL_NAME}")
    model = SentenceTransformer(MODEL_NAME)

    resultados = evaluar_corpus(CORPUS_67, canonical, model)
    imprimir_reporte(resultados)

    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(resultados, f, ensure_ascii=False, indent=2)
    print(f"\nDistribucion completa guardada en: {OUTPUT_JSON}")


if __name__ == "__main__":
    main()
