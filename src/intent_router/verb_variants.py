"""Variantes conjugadas de VERBOS_ACCION, escritas a mano (no stemming).

Cubre, cuando difieren del infinitivo:
- Imperativo informal (tu): "muestra", "cancela".
- Imperativo voseo caleño, solo cuando difiere del tu tras `normalize`
  (los verbos regulares colapsan a la misma forma al perder el acento;
  solo los que cambian de raiz, como "mostrar" -> "mostra", divergen).
- La forma con "-me" pegado cuando es un pedido natural dirigido al
  asistente: "mostrame", "dame", "avisame".
- Presente de primera persona para los verbos modales que casi nunca
  aparecen en infinitivo cuando son ellos mismos la accion: "quiero",
  "necesito", "puedo", "debo".

Cobertura deliberadamente parcial:
- "ver" no tiene variantes: su imperativo tu ("ve") es ambiguo con el
  imperativo de "ir" y con la palabra "ve"; se prefiere no adivinar.
- El "-me" se omite donde no suena natural en español caleño (iniciar,
  terminar, finalizar, encontrar, comenzar, empezar, reintentar,
  detener) en vez de forzarlo.
- Se excluye "para" (imperativo voseo de "parar"): es tambien la
  preposicion mas comun del idioma, y el falso positivo pesa mas que el
  beneficio. "parame" si se incluye porque no es ambiguo.

Algunas formas ("muestra", "alerta", "guia") tambien son sustantivos
comunes en español: esto puede marcar un candidato a verbo de accion en
un mensaje donde en realidad se uso como sustantivo. Es una señal
barata igual que el tripwire, no una confirmacion — el nivel que la usa
(router.py) decide cuanto confiar en un solo match.

NOTA: nombre de archivo provisional, no esta fijado en la tabla de
modulos del CLAUDE.md.
"""

from __future__ import annotations

from intent_router.lexicon import VERBOS_ACCION

VARIANTES_VERBO: dict[str, str] = {
    # querer
    "quiero": "querer",
    "queres": "querer",
    "quisiera": "querer",
    # necesitar
    "necesito": "necesitar",
    # poder
    "puedo": "poder",
    "podes": "poder",
    # deber
    "debo": "deber",
    # mostrar
    "muestra": "mostrar",
    "mostra": "mostrar",
    "muestrame": "mostrar",
    "mostrame": "mostrar",
    # consultar
    "consulta": "consultar",
    "consultame": "consultar",
    # revisar
    "revisa": "revisar",
    "revisame": "revisar",
    # chequear
    "chequea": "chequear",
    "chequeame": "chequear",
    # decir
    "di": "decir",
    "deci": "decir",
    "dime": "decir",
    "decime": "decir",
    "digo": "decir",
    # explicar
    "explica": "explicar",
    "explicame": "explicar",
    # informar
    "informa": "informar",
    "informame": "informar",
    # avisar
    "avisa": "avisar",
    "avisame": "avisar",
    # notificar
    "notifica": "notificar",
    "notificame": "notificar",
    # alertar
    "alerta": "alertar",
    "alertame": "alertar",
    # dar
    "da": "dar",
    "dame": "dar",
    "deme": "dar",
    "doy": "dar",
    # enviar
    "envia": "enviar",
    "enviame": "enviar",
    # mandar
    "manda": "mandar",
    "mandame": "mandar",
    # compartir
    "comparte": "compartir",
    "comparti": "compartir",
    "comparteme": "compartir",
    "compartime": "compartir",
    # activar
    "activa": "activar",
    "activame": "activar",
    # desactivar
    "desactiva": "desactivar",
    "desactivame": "desactivar",
    # encender
    "enciende": "encender",
    "encende": "encender",
    "enciendeme": "encender",
    "encendeme": "encender",
    # apagar
    "apaga": "apagar",
    "apagame": "apagar",
    # prender
    "prende": "prender",
    "prendeme": "prender",
    # cancelar
    "cancela": "cancelar",
    "cancelame": "cancelar",
    # confirmar
    "confirma": "confirmar",
    "confirmame": "confirmar",
    # aceptar
    "acepta": "aceptar",
    "aceptame": "aceptar",
    # rechazar
    "rechaza": "rechazar",
    "rechazame": "rechazar",
    # ayudar
    "ayuda": "ayudar",
    "ayudame": "ayudar",
    # guiar
    "guia": "guiar",
    "guiame": "guiar",
    # comparar
    "compara": "comparar",
    "comparame": "comparar",
    # buscar
    "busca": "buscar",
    "buscame": "buscar",
    # encontrar
    "encuentra": "encontrar",
    "encontra": "encontrar",
    # reportar
    "reporta": "reportar",
    "reportame": "reportar",
    # registrar
    "registra": "registrar",
    "registrame": "registrar",
    # cambiar
    "cambia": "cambiar",
    "cambiame": "cambiar",
    # actualizar
    "actualiza": "actualizar",
    "actualizame": "actualizar",
    # modificar
    "modifica": "modificar",
    "modificame": "modificar",
    # ajustar
    "ajusta": "ajustar",
    "ajustame": "ajustar",
    # configurar
    "configura": "configurar",
    "configurame": "configurar",
    # agregar
    "agrega": "agregar",
    "agregame": "agregar",
    # añadir
    "añade": "añadir",
    "añadi": "añadir",
    # quitar
    "quita": "quitar",
    "quitame": "quitar",
    # eliminar
    "elimina": "eliminar",
    "eliminame": "eliminar",
    # borrar
    "borra": "borrar",
    "borrame": "borrar",
    # iniciar
    "inicia": "iniciar",
    # comenzar
    "comienza": "comenzar",
    "comenza": "comenzar",
    # empezar
    "empieza": "empezar",
    "empeza": "empezar",
    # terminar
    "termina": "terminar",
    # finalizar
    "finaliza": "finalizar",
    # parar
    "parame": "parar",
    # detener
    "deten": "detener",
    "detene": "detener",
    # repetir
    "repite": "repetir",
    "repeti": "repetir",
    "repiteme": "repetir",
    "repetime": "repetir",
    # reintentar
    "reintenta": "reintentar",
}


def resolver_verbo(token: str) -> str | None:
    """Devuelve el infinitivo de `token` si es un verbo de accion (ya sea
    el infinitivo mismo o una variante conocida en VARIANTES_VERBO), o
    None si no lo es.

    No corrige typos: eso es responsabilidad de `typo_fallback`, pensado
    como paso posterior cuando esta funcion devuelve None.
    """
    if token in VERBOS_ACCION:
        return token
    return VARIANTES_VERBO.get(token)
