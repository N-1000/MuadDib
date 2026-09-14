# CLAUDE.md — MuadDib (Fase 1: algoritmo core)

Instrucciones para Claude Code en este repositorio.

## Dónde estamos

Construyendo `intent_router/` como paquete standalone: la cascada de 3 niveles (reglas → embeddings → LLM) sin cliente real conectado todavía. EcoPulse es el primer caso de uso, pero nada del core debe conocer nada de EcoPulse — eso vive en `clients/`. Lo de aislamiento multi-cliente, ciclo de aprendizaje supervisado y cumplimiento normativo es fase posterior; no está en este archivo a propósito, no lo reintroduzcas hasta que se pida explícitamente.

## Cómo trabajar en este repo

- Español, directo, sin preámbulos.
- Honestidad técnica sobre validación: si algo tiene un riesgo o una alternativa mejor, decilo con su razón.
- Código funcional de punta a punta. Si algo queda a medias, decirlo y listar qué falta.

## Comentarios

Esta sección aplica a código de producción (`src/`). En tests el criterio es otro: ver más abajo.

- Cero comentarios inline dentro del cuerpo de una función, sin excepción. Si hace falta explicar el *porqué* de algo no obvio, se extrae a una función privada con nombre descriptivo — el nombre reemplaza al comentario.
- Docstrings de una sola línea. Si necesitás más de una línea para explicar qué hace una función, la función está haciendo demasiado: dividirla, no documentarla.
- Docstring de módulo: opcional, máximo una línea.

### Comentarios en tests

En un test, el "por qué existe este caso" es contexto que no se puede mover a un nombre de función. Se permite un comentario breve cuando explica por qué el caso existe (no qué hace la línea).

## Caracteres no imprimibles

Nunca escribir un carácter invisible o no imprimible como literal en el código fuente: combinantes Unicode, BOM, control chars, sentinels de zona de uso privado. Siempre secuencia de escape (`"\u0303"`, `"\ufeff"`, `"\x00"`). Un carácter que no se ve al leer el archivo es un bug esperando a que un editor, un copy/paste o una normalización del repo se lo coma sin dejar rastro.

## Módulos a construir (contrato)

| Archivo | Función | Contrato |
|---|---|---|
| `normalizer.py` | `normalize(texto) -> str` | Pura. minúsculas, NFD + quitar diacríticos, **ñ protegida** (`año` ≠ `ano`). |
| `lexicon.py` | `VERBOS_ACCION`, `CONECTORES`, `NEGACIONES` | Tres `frozenset[str]` cerrados, en la forma que produce `normalize`. |
| `tripwire.py` | `detectar_senales(texto_normalizado) -> SenalTripwire` | Marca conector/negación presentes, sin interpretar. |
| `splitter.py` | `dividir_por_conectores(texto_normalizado) -> list[str]` | Split literal en cláusulas por `CONECTORES`. |
| `verb_variants.py` | `resolver_verbo(token) -> str \| None` | Infinitivo directo o vía variante escrita a mano (no stemming). |
| `typo_fallback.py` | `corregir_typo(token, vocabulario) -> str \| None` | Fallback de typos (rapidfuzz); `None` si el match es ambiguo. |
| `rules.py` | `analizar(mensaje) -> AnalisisNivel0` | Orquesta los cinco de arriba sobre un mensaje crudo, sin conocer `config` todavía. |
| `entities.py` | `extract_entities(texto, config) -> dict` | Detecta por keyword contra un conjunto conocido en `config`. |
| `embeddings.py` | `load_model()` | Carga una sola vez al iniciar, nunca por request. |
| `embeddings.py` | `encode(texto) -> vector` | |
| `embeddings.py` | `precompute_canonical(config) -> matriz` | Embeddings de todas las frases canónicas, precalculados al arranque. |
| `router.py` | `resolve(mensaje, config) -> Decision` | Orquesta 0→1→2. `Decision` es un objeto explícito (intención, nivel, confianza, entidades, acción) — **nunca un string**. |
| `metrics.py` | `log_decision(evento)` / `hit_rate()` | Logging estructurado desde ya: nivel, intención, confianza, entidades, latencia. |

Nombres de módulo/carpeta ya definidos en la doc técnica del proyecto — no son provisionales. Nombres de variables/funciones internas que no estén en esta tabla sí son provisionales, marcalos como tal.

## Capa determinista — orden de construcción

1. Normalización (`unicodedata`, ñ protegida). Pura, con tests.
2. Tres listas (verbos-acción, conectores, negaciones) en `set` — O(1), sin dependencias.
3. Tripwire estructural: conector → posible multi-intención; negación → posible exclusión. No interpreta, solo marca cuándo no confiar en un solo match.
4. Split por conectores.
5. `rapidfuzz` (MIT) solo como fallback de typos, umbral alto.
6. Variantes de verbo listadas a mano, no stemming.

**No usar:** `unidecode` (rompe la ñ), `fuzzywuzzy` (GPL), `flashtext`/`pyahocorasick` (overkill a esta escala), parsing sujeto-verbo-objeto completo, reglas a mano de negación lejana.

**Pospuesto, no descartado:** spaCy (`es_core_news_sm`) solo en la rama que el tripwire dispare, y solo cuando los datos muestren que las listas no alcanzan. No lo construyas todavía aunque parezca "más completo".

## Reglas de arquitectura (no negociables)

1. Dirección de dependencia única: `agent_core.py → intent_router`. El router nunca importa el agente ni nada de `clients/`.
2. Config inyectada como parámetro, nunca importada directo — aunque hoy exista un solo cliente.
3. Lógica del algoritmo idéntica para todos los clientes; solo cambian los datos de la configuración del cliente (ej: `rules_nivel0.yaml`).
4. Lo que la config declarativa no cubra va en extensiones aisladas, nunca como código custom dentro del core.
5. Esquema fijo de la configuración del cliente completo desde ya, incluyendo `sensitive: bool` — aunque el flujo de revisión que lo consume (ciclo de aprendizaje) todavía no exista. El campo es gratis ahora; migrarlo después no lo es.

## Comportamiento del router (aplica ya, no es "seguridad de producción")

- Deny-by-default: el router solo reconoce intenciones conocidas; el resto cae a fallback o LLM.
- Ante error o timeout del LLM (Nivel 2), degradar a respuesta segura — nunca colgar ni ejecutar una acción con efecto real por default.
- Entidades siempre validadas contra un conjunto conocido; la acción se elige de un set fijo, nunca se arma con texto libre.
- Una intención `sensitive: true` puede detectarse en la capa barata pero no auto-ejecutarse — el dato que devuelve la clasificación lleva esa restricción, no depende de que alguien se acuerde de chequearla en otro lado.

## Tests

- Correr la suite: `uv run pytest`
- `normalize()` y `extract_entities()` son funciones puras: cobertura alta, casos borde (tildes, emojis, cadena vacía, mensajes larguísimos).
- Property-based con `hypothesis` sobre las funciones puras. Invariantes de `normalize()`: idempotencia, `len(salida) <= longitud_maxima`, ningún carácter de categoría Unicode `Mn` en la salida y la ñ sobrevive.
- **Si un test falla, se arregla la función, no el test.** No agregar `assume()` ni relajar una aserción para que pase. Si creés que un caso de aceptación está mal, pedí autorización antes de cambiarlo.
- Si `hypothesis` encuentra un contraejemplo, reportarlo con el input exacto antes de modificar test o función.
- No dar una tarea por terminada con tests en rojo.

## Casos de aceptación — `normalize()`

Contrato fijo. Claude Code no agrega ni cambia casos acá sin pedirlo primero. Un bug encontrado en `normalize()` siempre se congela como caso nuevo en esta lista.

```
normalize("año")           == "año"
normalize("AÑO")           == "año"
normalize("ano")           == "ano"
normalize("camión")        == "camion"
normalize("")              == ""
normalize("a" * 5000)      -> longitud 2000
normalize("hola\x00mundo") == "holamundo"
normalize("N" + "\u0303")  == "ñ"   (ñ en forma NFD: N + tilde combinante)

normalize(123)                        -> TypeError
normalize("hola", longitud_maxima=0)  -> ValueError
```

El sentinel usado para proteger la ñ debe ser un codepoint de zona de uso privado (categoría Unicode `Co`), nunca vacío. Assert a nivel de módulo que lo verifique al importar.

## Qué NO entra acá (deliberado, no un olvido)

Aislamiento multi-cliente, ciclo de aprendizaje supervisado (cola de revisión, clustering de candidatos), Ley 1581/Habeas Data, gestión de secretos de tools de cliente, rate limiting. Todo esto está documentado en la base de conocimiento del proyecto. Entra a este archivo cuando arranque la fase de multi-client hardening — no antes.
