from pathlib import Path
import yaml
from eval_corpus_baseline import CORPUS_67, CANONICAL_PATH
from intent_router.config_loader import cargar_config
from intent_router.embeddings import MODEL_DEFAULT, load_model, precompute_canonical
from intent_router.router import Decision, _evaluar_nivel1, resolve

CONFIG_PATH = Path(__file__).resolve().parent / "clients" / "ecopulse" / "config.yaml"
RULES_PATH = Path(__file__).resolve().parent / "clients" / "ecopulse" / "rules_nivel0.yaml"


def cargar_canonical_embeddings(modelo):
    with open(CANONICAL_PATH, "r", encoding="utf-8") as f:
        canonical_yaml = yaml.safe_load(f)
    return precompute_canonical({"intents": canonical_yaml.get("intents", [])}, modelo)


def es_acierto(decision: Decision, esperado) -> bool | None:
    if esperado is None or decision.intencion is None:
        return None
    if isinstance(esperado, list):
        return decision.intencion in esperado
    return decision.intencion == esperado


def cargar_dependencias() -> tuple[dict, object]:
    config = cargar_config(CONFIG_PATH, RULES_PATH)
    modelo = load_model(MODEL_DEFAULT)
    if modelo is None:
        raise RuntimeError("No se pudo cargar el modelo de embeddings; no se puede medir la cascada real.")
    canonical_data = cargar_canonical_embeddings(modelo)
    return config, canonical_data


def medir_cascada(config: dict, canonical_data) -> list[dict]:
    filas = []
    for item in CORPUS_67:
        resultado = resolve(item["mensaje"], config, canonical_data=canonical_data)
        for decision in resultado.decisiones:
            filas.append({
                "mensaje": item["mensaje"],
                "bloque": item["bloque"],
                "esperado": item["esperado"],
                "decision": decision,
            })
    return filas


def medir_bypass_nivel0(filas_n0: list[dict], config: dict, canonical_data) -> list[dict]:
    """Para cada clausula resuelta en Nivel 0, evalua que haria Nivel 1 si Nivel 0 no la interceptara."""
    umbral = float(config["routing"]["threshold"])
    margen_min = float(config["routing"]["min_margin"])

    bypass = []
    for f in filas_n0:
        decision_bypass = _evaluar_nivel1(f["decision"].clausula, False, canonical_data, umbral, margen_min)
        bypass.append({**f, "decision_bypass": decision_bypass})
    return bypass


def imprimir_reporte(filas: list[dict], config: dict, canonical_data) -> None:
    total_mensajes = len(CORPUS_67)
    total_clausulas = len(filas)

    print("=" * 95)
    print("MEDICION DE LA CASCADA REAL (resolve() con config.yaml + rules_nivel0.yaml + canonical.yaml)")
    print(f"Mensajes de entrada: {total_mensajes} | Clausulas efectivamente enrutadas: {total_clausulas}")
    print("=" * 95)

    n0 = [f for f in filas if f["decision"].nivel == 0]
    n1 = [f for f in filas if f["decision"].nivel == 1]
    n2 = [f for f in filas if f["decision"].nivel == 2]

    print(f"\n1. RESUELTOS EN NIVEL 0 (Reglas deterministas): {len(n0)}/{total_clausulas} ({len(n0)/total_clausulas*100:.1f}%)")
    print("   (esperado usa el vocabulario de canonical.yaml, no el de rules_nivel0.yaml;")
    print("    el chequeo es 'la accion despachada es la que el usuario queria', no un match de nombre)")
    aciertos_n0 = [es_acierto(f["decision"], f["esperado"]) for f in n0]
    juzgables_n0 = [a for a in aciertos_n0 if a is not None]
    if juzgables_n0:
        print(f"   - Precision en Nivel 0 (excluye saludos, sin intent esperado): {sum(juzgables_n0)}/{len(juzgables_n0)} ({sum(juzgables_n0)/len(juzgables_n0)*100:.1f}% aciertos)")
    for f, ok in zip(n0, aciertos_n0):
        d = f["decision"]
        ok_tag = "-" if ok is None else ("OK" if ok else "FALLO")
        origen = "" if d.clausula == f["mensaje"] else f"  [clausula de: '{f['mensaje']}']"
        print(f"   - [{ok_tag}] '{d.clausula}' -> {d.intencion} | Esp: {f['esperado']}{origen}")

    n0_con_esperado = [f for f, ok in zip(n0, aciertos_n0) if ok is not None]
    if n0_con_esperado:
        print(f"\n   BYPASS: que haria Nivel 1 si Nivel 0 no interceptara estas {len(n0_con_esperado)} clausulas")
        print("   (mide el costo real de sacar estas phrases de rules_nivel0.yaml: si N1 ya acierta,")
        print("    el costo es cero; si N1 tambien falla o escala, el error se mueve de capa)")
        bypass = medir_bypass_nivel0(n0_con_esperado, config, canonical_data)
        n1_hubiera_acertado = 0
        for f in bypass:
            d0 = f["decision"]
            db = f["decision_bypass"]
            ok_bypass = es_acierto(db, f["esperado"])
            if db.nivel == 1:
                resultado_str = f"resuelve: {db.intencion} (confianza={db.confianza:.4f}) -> {'OK' if ok_bypass else 'FALLO'}"
                if ok_bypass:
                    n1_hubiera_acertado += 1
            else:
                resultado_str = f"escala: {' + '.join(db.motivos_escalada)}"
            print(f"   - '{d0.clausula}' | Nivel0 dio: {d0.intencion} (Esp: {f['esperado']}) | Nivel1 bypass: {resultado_str}")
        print(f"   - Resumen: de {len(n0_con_esperado)} hijacks de Nivel 0, Nivel 1 hubiera acertado en {n1_hubiera_acertado}")

    print(f"\n2. RESUELTOS EN NIVEL 1 (Embeddings): {len(n1)}/{total_clausulas} ({len(n1)/total_clausulas*100:.1f}%)")
    aciertos = [es_acierto(f["decision"], f["esperado"]) for f in n1]
    juzgables = [a for a in aciertos if a is not None]
    if juzgables:
        print(f"   - Precision en Nivel 1: {sum(juzgables)}/{len(juzgables)} ({sum(juzgables)/len(juzgables)*100:.1f}% aciertos)")
    for f, ok in zip(n1, aciertos):
        d = f["decision"]
        ok_tag = "-" if ok is None else ("OK" if ok else "FALLO")
        print(f"   - [{ok_tag}] '{d.clausula}' -> {d.intencion} (confianza={d.confianza:.4f}) | Esp: {f['esperado']}")

    print(f"\n3. ESCALADOS A NIVEL 2 (LLM): {len(n2)}/{total_clausulas} ({len(n2)/total_clausulas*100:.1f}%)")
    razones: dict[str, int] = {}
    for f in n2:
        for razon in f["decision"].motivos_escalada:
            razones[razon] = razones.get(razon, 0) + 1
    for razon, cnt in razones.items():
        print(f"   - {razon}: {cnt} casos")

    print("\nDetalle de clausulas escaladas a Nivel 2:")
    for f in n2:
        d = f["decision"]
        motivo = " + ".join(d.motivos_escalada) if d.motivos_escalada else "-"
        print(f"   * '{d.clausula}' -> Candidato: {d.intencion} | Motivo: {motivo}")

    ahorro_total = (len(n0) + len(n1)) / total_clausulas * 100
    print("\n" + "=" * 95)
    print(f"AHORRO TOTAL DE LLM (Nivel 0 + Nivel 1): {ahorro_total:.1f}% de las clausulas resueltas localmente")
    print(f"TRAFICO QUE CONSUME LLM (Nivel 2):       {len(n2)/total_clausulas*100:.1f}%")
    print("=" * 95)


def main() -> None:
    config, canonical_data = cargar_dependencias()
    filas = medir_cascada(config, canonical_data)
    imprimir_reporte(filas, config, canonical_data)


if __name__ == "__main__":
    main()
