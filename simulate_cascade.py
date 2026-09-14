import json
from pathlib import Path
import yaml
from eval_corpus_baseline import CORPUS_67, CANONICAL_PATH, OUTPUT_JSON as BASELINE_JSON
from intent_router.rules import analizar


def cargar_sensitive_intents(ruta: Path) -> set[str]:
    with open(ruta, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return {item["name"] for item in data.get("intents", []) if item.get("sensitive", False)}


def tiene_clausula_negada(mensaje: str) -> bool:
    analisis = analizar(mensaje)
    return any(c.negada for c in analisis.clausulas)


def simular_cascada(umbral_theta=0.60, margen_min=0.05):
    with open(BASELINE_JSON, "r", encoding="utf-8") as f:
        baseline_data = json.load(f)

    sensitive_intents = cargar_sensitive_intents(CANONICAL_PATH)

    # Identificar mensajes que resuelve Nivel 0 segun las reglas conocidas
    # Saludos (6 exactos) y las 3 frases del rules_nivel0.yaml que matchean literal
    nivel0_mensajes = {
        "Hola", "Buenas tardes", "Gracias", "Chao", "Como estas", "Todo bien por aca",
        "Mostrame la calidad del aire de hoy",  # matchea mostrar + aire
        "Dame el reporte semanal",             # matchea dar + reporte
        "Activa las alertas de contaminacion", # matchea activar + alerta (sensitive en N0)
    }

    resueltos_n0 = []
    resueltos_n1 = []
    escalados_a_n2 = []

    for item in baseline_data:
        msg = item["mensaje"]
        s1 = item["s1"]
        delta = item["delta"]
        top1 = item["top1_intent"]
        bloque = item["bloque"]
        esperado = item["esperado"]

        # 1. Paso por Nivel 0
        if msg in nivel0_mensajes:
            resueltos_n0.append({
                "mensaje": msg,
                "nivel": "Nivel 0",
                "razon": "Regla determinista / exact-match",
                "intencion": esperado if esperado else "saludo_cortesia",
            })
            continue

        # 2. Paso por Nivel 1 (Embeddings)
        # Condiciones de fallo/escalada de N1 (independientes, igual que router.py):
        # a) Intencion sensible: N1 no puede resolverla
        es_sensible = top1 in sensitive_intents

        # b) Confianza insuficiente
        confianza_baja = s1 < umbral_theta

        # c) Ambiguedad
        ambiguo = delta < margen_min

        # d) Clausula negada: N1 no puede resolverla, igual que sensitive
        negada = tiene_clausula_negada(msg)

        razones_activas = []
        if es_sensible:
            razones_activas.append("Bloqueo fail-safe: intencion sensitive=true en Nivel 1")
        if confianza_baja:
            razones_activas.append(f"Confianza baja (s1={s1:.4f} < theta={umbral_theta:.2f})")
        if ambiguo:
            razones_activas.append(f"Margen ambiguo (delta={delta:+.4f} < margen_min={margen_min:.2f})")
        if negada:
            razones_activas.append("Clausula negada: bloqueo fail-safe en Nivel 1")

        if razones_activas:
            escalados_a_n2.append({
                "mensaje": msg,
                "bloque": bloque,
                "esperado": esperado,
                "candidato_n1": top1,
                "s1": s1,
                "delta": delta,
                "razones": razones_activas,
            })
        else:
            # Resuelto por Nivel 1
            acierto_n1 = (top1 == esperado) if esperado else False
            resueltos_n1.append({
                "mensaje": msg,
                "bloque": bloque,
                "esperado": esperado,
                "intencion_n1": top1,
                "s1": s1,
                "delta": delta,
                "acierto": acierto_n1,
            })

    total = len(baseline_data)
    print("=" * 95)
    print(f"SIMULACION DE ENRUTAMIENTO EN CASCADA (Total: {total} mensajes)")
    print(f"Parametros N1: umbral_theta = {umbral_theta:.2f}, margen_min = {margen_min:.2f}")
    print("=" * 95)

    print(f"\n1. RESUELTOS EN NIVEL 0 (Reglas / Saludos): {len(resueltos_n0)}/{total} ({len(resueltos_n0)/total*100:.1f}%)")
    for r in resueltos_n0:
        print(f"   - '{r['mensaje']}' -> {r['intencion']}")

    print(f"\n2. RESUELTOS EN NIVEL 1 (Embeddings): {len(resueltos_n1)}/{total} ({len(resueltos_n1)/total*100:.1f}%)")
    n1_aciertos = sum(1 for r in resueltos_n1 if r["acierto"])
    print(f"   - Precision en Nivel 1: {n1_aciertos}/{len(resueltos_n1)} ({n1_aciertos/len(resueltos_n1)*100:.1f}% aciertos)")
    for r in resueltos_n1:
        ok_tag = "OK" if r["acierto"] else "FALLO"
        print(f"   - [{ok_tag}] '{r['mensaje']}' -> {r['intencion_n1']} (s1={r['s1']:.4f}, delta={r['delta']:+.4f}) | Esp: {r['esperado']}")

    print(f"\n3. ESCALADOS A NIVEL 2 (LLM): {len(escalados_a_n2)}/{total} ({len(escalados_a_n2)/total*100:.1f}%)")
    razones = {}
    for r in escalados_a_n2:
        for razon in r["razones"]:
            r_tipo = razon.split("(")[0].strip()
            razones[r_tipo] = razones.get(r_tipo, 0) + 1
    for razon, cnt in razones.items():
        print(f"   - {razon}: {cnt} casos")

    print("\nDetalle de mensajes escalados a Nivel 2:")
    for r in escalados_a_n2:
        motivo = " + ".join(r["razones"])
        print(f"   * '{r['mensaje']}' -> Motivo: {motivo} (Candidato: {r['candidato_n1']})")

    ahorro_total = (len(resueltos_n0) + len(resueltos_n1)) / total * 100
    print("\n" + "=" * 95)
    print(f"AHORRO TOTAL DE LLM (Nivel 0 + Nivel 1): {ahorro_total:.1f}% del trafico resuelto localmente")
    print(f"TRAFICO QUE CONSUME LLM (Nivel 2):       {len(escalados_a_n2)/total*100:.1f}%")
    print("=" * 95)


if __name__ == "__main__":
    simular_cascada()
