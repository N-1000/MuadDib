"""Listas cerradas de palabras para la capa determinista del router.

Verbos de accion, conectores y negaciones del espanol (incluye registro
caleño coloquial). Pertenencia en O(1) via frozenset, sin dependencias
externas. Son un punto de partida: hay que ajustarlas con mensajes reales
de usuarios cuando exista un dataset (ver CLAUDE.md, capa deterministica).

Todas las entradas estan en la misma forma que produce
`intent_router.normalizer.normalize`: minusculas, sin acentos (la ñ se
preserva), una sola palabra por entrada. Las variantes conjugadas de cada
verbo (voseo caleño, imperativo, etc.) son responsabilidad del siguiente
paso de la cascada, no de esta lista.

NOTA: nombre de archivo provisional, no esta fijado en la tabla de
modulos del CLAUDE.md.
"""

VERBOS_ACCION: frozenset[str] = frozenset(
    {
        "querer",
        "necesitar",
        "poder",
        "deber",
        "mostrar",
        "ver",
        "consultar",
        "revisar",
        "chequear",
        "decir",
        "explicar",
        "informar",
        "avisar",
        "notificar",
        "alertar",
        "dar",
        "enviar",
        "mandar",
        "compartir",
        "activar",
        "desactivar",
        "encender",
        "apagar",
        "prender",
        "cancelar",
        "confirmar",
        "aceptar",
        "rechazar",
        "ayudar",
        "guiar",
        "comparar",
        "buscar",
        "encontrar",
        "reportar",
        "registrar",
        "cambiar",
        "actualizar",
        "modificar",
        "ajustar",
        "configurar",
        "agregar",
        "añadir",
        "quitar",
        "eliminar",
        "borrar",
        "iniciar",
        "comenzar",
        "empezar",
        "terminar",
        "finalizar",
        "parar",
        "detener",
        "repetir",
        "reintentar",
    }
)

CONECTORES: frozenset[str] = frozenset(
    {
        "y",
        "tambien",
        "ademas",
        "o",
        "pero",
        "sino",
        "aunque",
        "mientras",
        "despues",
        "luego",
        "entonces",
        "aparte",
        "asimismo",
    }
)

NEGACIONES: frozenset[str] = frozenset(
    {
        "no",
        "nunca",
        "jamas",
        "tampoco",
        "ni",
        "nada",
        "ningun",
        "ninguna",
        "ninguno",
    }
)
