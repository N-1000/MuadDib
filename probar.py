import sys

from intent_router.rules import analizar


def main() -> None:
    total_mensajes = 0
    mensajes_sin_verbo = 0
    total_clausulas = 0
    clausulas_sin_verbo = 0

    for linea in sys.stdin:
        texto = linea.strip()
        if not texto:
            continue

        total_mensajes += 1
        resultado = analizar(texto)
        verbos = [clausula.verbo for clausula in resultado.clausulas]

        for verbo in verbos:
            total_clausulas += 1
            if verbo is None:
                clausulas_sin_verbo += 1

        if all(verbo is None for verbo in verbos):
            mensajes_sin_verbo += 1
            marca = "SIN VERBO"
        else:
            marca = "ok"

        print(f"[{marca}] {texto!r} -> {verbos}")

    print("=" * 70)
    print(f"mensajes totales: {total_mensajes}")
    if total_mensajes:
        print(
            f"mensajes sin ningun verbo resuelto: {mensajes_sin_verbo} "
            f"({mensajes_sin_verbo / total_mensajes:.1%})"
        )
    print(f"clausulas totales: {total_clausulas}")
    if total_clausulas:
        print(
            f"clausulas con verbo=None: {clausulas_sin_verbo} "
            f"({clausulas_sin_verbo / total_clausulas:.1%})"
        )


if __name__ == "__main__":
    main()
