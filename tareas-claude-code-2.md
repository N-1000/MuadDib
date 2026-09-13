# Tareas Claude Code — tanda 2 (revisión de tests)

Pasarlas de a una. Las tareas 1 y 2 son las urgentes.

---

## Tarea 1 — El test del sentinel no prueba nada

En `tests/test_normalizer.py`, `test_intento_de_inyectar_marcador_interno`
define `caracter_marcador_interno = ""` — string vacío. El f-string colapsa a
`normalize("holamundo")` y las dos aserciones pasan trivialmente. El test no
ejercita el caso que dice cubrir.

Arreglo: importar el sentinel real desde el módulo (`from intent_router.normalizer
import _SENTINEL_ENIE` o el nombre que tenga) y usar esa constante en el test.
No redefinirlo como literal local — si se importa, no puede desincronizarse del
módulo.

Después de arreglarlo, verificá que el test **falle** si le quitás la línea que
protege contra el sentinel inyectado en `normalize()`. Si sigue en verde sin esa
protección, el test sigue sin servir. Reportá el resultado de esa verificación.

---

## Tarea 2 — Congelar el caso NFD y subir max_examples

Dos cosas sobre el bug que encontró hypothesis (la Ñ en forma descompuesta):

a) Agregar a `tests/test_normalize_acceptance.py` el caso:

       normalize("N" + "\u0303") == "ñ"

   Un bug encontrado se convierte en caso de aceptación fijo, siempre.

b) En `tests/test_normalize_properties.py`, agregar `@settings(max_examples=1000)`
   a las tres propiedades. Hoy corren con el default (100) y por eso el bug NFD
   no apareció en el run normal.

---

## Tarea 3 — Deduplicar test_normalizer.py

Seis casos están duplicados entre `test_normalizer.py` y
`test_normalize_acceptance.py`: "año", "AÑO", caracteres de control, TypeError,
ValueError, string vacío.

`test_normalize_acceptance.py` es el contrato congelado y manda. Sacá esos seis
de `test_normalizer.py` y dejá ahí solo lo que agrega valor propio: "Ñoño",
"café"/"acción"/"múltiple", puntuación y números, truncado con `longitud_maxima`
explícito, y el test del sentinel ya arreglado en la tarea 1.

---

## Tarea 4 — Ambigüedad en corregir_typo()

`corregir_typo()` hoy devuelve un match aunque el token esté a distancia
parecida de dos verbos distintos del vocabulario. Devuelve un resultado con la
misma confianza aparente que un match limpio, y quien lo consume no puede
distinguir.

Eso es la zona gris que el estándar de seguridad del proyecto dice que no debe
existir: si una de las dos candidatas mapea a una acción sensible, un typo
elegido a propósito puede empujar la clasificación hacia ella.

Cambiar la función para que, cuando las dos mejores candidatas estén dentro de
un margen chico entre sí, devuelva `None` en vez de elegir. El margen es un
parámetro con default explícito, no un número mágico enterrado.

Agregar tests de: caso ambiguo → `None`, caso con ganador claro → corrige
normalmente. Pará y consultá antes de fijar el valor del margen — no lo elijas
solo.

---

## Tarea 5 — Tests frágiles y nombres que mienten

- `test_umbral_personalizado_es_mas_permisivo` depende del score interno de
  rapidfuzz (~78). Un bump de versión de la librería lo rompe sin que cambie
  nuestra lógica. Reescribirlo para que verifique la relación (con umbral bajo
  corrige, con el default no) sin depender del número exacto.
- `test_varios_conectores_dividen_en_varias_clausulas` dice "varias" y verifica
  dos cláusulas. O renombralo, o agregá el caso de tres o más.
- En `test_normalize_properties.py`, la tercera propiedad asume que el texto
  nunca se trunca (`max_size=200` vs `longitud_maxima=2000`). Si alguien sube
  ese `max_size` la propiedad falla por una razón ajena al bug que busca.
  Hacerla explícita sobre ese supuesto.

---

## Tarea 6 — Regla de comentarios en tests

Los tests tienen comentarios inline (`test_lexicon.py`, `test_typo_fallback.py`,
`test_verb_variants.py`), lo que contradice la regla de `CLAUDE.md` de cero
comentarios inline.

Decisión: la regla aplica a código de producción, no a tests. En un test, el
"por qué existe este caso" es contexto que no se puede mover a un nombre de
función.

Actualizar la sección Comentarios de `CLAUDE.md` para que diga explícitamente
que la regla es para código de producción, y que en tests se permite un
comentario breve cuando explica por qué el caso existe (no qué hace la línea).
No tocar los comentarios existentes en los tests.
