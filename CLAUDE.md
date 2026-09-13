# CLAUDE.md — MuadDib

Instrucciones para Claude Code en este repositorio. Leelas en cada sesión y respetalas al generar o modificar código.

---

## Qué es este proyecto

MuadDib es un *intent router* híbrido en cascada (reglas → embeddings → LLM) que clasifica la intención de cada mensaje y elige la acción correspondiente. Primera implementación real: EcoPulse AI (asistente ambiental para la red de sensores Tángara, Cali). Está pensado para extraerse luego como paquete reutilizable para otros clientes.

**Objetivo:** enrutar cada mensaje a la respuesta correcta de la forma más barata, controlada y auditable posible. Reducir el consumo de LLM es la palanca; el fin es hacer económicamente viable desplegar agentes para muchos clientes. Existe por tres razones que pesan juntas: **costo** (resolver local lo que se pueda), **control/seguridad** (rutas deterministas, auditables, no jailbrikeables), **escalabilidad multi-cliente** (mismo core, solo cambia config).

## Cómo trabajar en este repo

- Respondé en **español**.
- **Directo**, sin preámbulos. Ejemplos concretos por encima de teoría.
- **Honestidad técnica sobre validación:** si algo tiene un riesgo, un error o una alternativa mejor, decilo con su razón, aunque contradiga una decisión ya tomada. No des por buena una idea solo porque está en marcha.
- **Entregables completos:** código funcional de punta a punta. Si algo queda a medias, decilo y listá qué falta.
- **Específico primero:** no generalices para multi-cliente sin al menos 2 casos reales. No sobre-diseñes antes de tiempo.
- Acompañá todo código con **tests**.

## Convención de nombres (PENDIENTE)

La convención de nombres del proyecto **todavía no está definida**. Todos los nombres de archivos, módulos, funciones, variables y campos que aparecen abajo son **provisionales y renombrables** — tratalos como descripciones de responsabilidad, no como nombres decididos. Antes de fijar nombres en código nuevo, o proponé opciones y esperá confirmación, o preguntá la convención. No ancles el diseño a ningún nombre sin aprobación.

## Reglas de arquitectura (no negociables)

1. **Dirección de dependencia única:** el agente consume al router; el router **nunca** importa el agente ni los modelos de la app.
2. **Config inyectada, nunca importada:** el router recibe la configuración del cliente como parámetro. Nunca importa la config de un cliente específico directamente.
3. **Core inmutable vs config por cliente:** la lógica del algoritmo es idéntica para todos; solo cambian los datos de configuración. El esquema de la config tiene los mismos campos fijos para cualquier cliente.
4. **Nada de espagueti:** lo que la config declarativa no cubra va en extensiones aisladas, nunca como código custom dentro del core.
5. **La decisión del router es un objeto explícito y auditable** (intención, nivel que resolvió, confianza, entidades, acción) — nunca solo un string.

## Capa determinista — alcance y stack

Principio: la inversión va a que la búsqueda sea más **inteligente**, no más **rápida** (ya es instantánea a esta escala).

**Construir (en este orden):**

1. **Normalización robusta con la ñ protegida.** `unicodedata` de la stdlib (NFD + quitar diacríticos), preservando la ñ (`año` ≠ `ano`). Función pura, con tests.
2. **Tres listas para español caleño:** verbos-acción, conectores, negaciones. Pertenencia en un `set` (O(1)). Sin dependencias.
3. **Señales estructurales baratas (tripwire):** detectar por lista si hay conector (posible multi-intención) o negación (posible exclusión), para saber cuándo NO confiar en un solo match.
4. **Split por conectores** para frases ordenadas.
5. **rapidfuzz** (MIT) solo como *fallback* de typos, con umbral alto y en tokens que lo ameriten.
6. **Variantes de verbo listadas a mano**, no stemming.

**No hacer:**

- No parsear sujeto-verbo-objeto completo en la normalización (pozo sin fondo; se paga en cada mensaje trivial).
- No escribir reglas a mano de negación lejana (reinventa un parser peor; eso va al modelo).
- No optimizar la velocidad de búsqueda (ya es instantánea).
- No usar flashtext/pyahocorasick/Aho-Corasick (overkill a esta escala).
- No usar unidecode (elimina la ñ) ni fuzzywuzzy (licencia GPL — trampa para producto cerrado).

**Posponer (solo cuando los datos lo pidan):** modelo spaCy en español (`es_core_news_sm`) como capa adicional —no base— solo en la rama que el tripwire dispare, para negación lejana y multi-intención enredada.

**Licencias seguras para producto cerrado:** stdlib (Python), rapidfuzz (MIT), pyahocorasick (BSD), NLTK (Apache 2.0). Evitar fuzzywuzzy (GPL).

## Seguridad y calidad (siempre activas)

- **Validá y saneá toda entrada externa:** mensaje del usuario (límite de longitud, normalización, sin caracteres de control), config al arranque (esquema estricto; si es inválida, el servicio no arranca), y candidatos del ciclo de aprendizaje.
- **Fail-safe:** ante error o timeout, degradar a estado seguro (respuesta genérica o handoff a humano), nunca ejecutar una acción con efecto real.
- **Enrutamiento protegido (deny-by-default):** el router solo reconoce intenciones conocidas; el resto cae a fallback o LLM.
- **Acciones sensibles con compuerta:** una intención con efecto real puede detectarse en la capa barata pero **no ejecutarse sola** — exige confianza alta y/o confirmación, o escala. La protección vive en el dato que devuelve la clasificación, no en que alguien se acuerde de chequearla.
- **Entidades validadas contra un conjunto conocido:** nunca armar una acción con texto libre del usuario; elegir la acción de un set fijo.
- **Aislamiento por cliente:** datos, config, candidatos de aprendizaje y límites de un cliente jamás se filtran a otro. El aprendizaje es por cliente, nunca global.
- **Ciclo de aprendizaje = superficie de ataque:** nunca auto-aprobar; múltiples señales de riesgo; acciones sensibles siempre a revisión humana.
- **Sin secretos** en código ni en config versionada (usar variables de entorno).
- **Privacidad (Ley 1581 de 2012, Colombia):** si se persisten mensajes identificables, recolectar lo mínimo, definir retención/borrado, anonimizar donde se pueda.
- **Logging estructurado y métricas desde el día 1** (nivel que resolvió, intención, confianza, latencia; hit rate por nivel). Alertar sobre degradación de tendencia, no solo errores duros.

**Definición de "hecho" (antes de dar por terminado un cambio):**

- [ ] Entrada validada y saneada donde corresponde.
- [ ] Tests unitarios nuevos/actualizados en verde.
- [ ] Dataset de regresión en verde si se tocaron frases/intenciones.
- [ ] Sin secretos en el diff.
- [ ] La decisión sigue siendo auditable.
- [ ] Acciones sensibles siguen exigiendo confianza alta / confirmación.
- [ ] Respeta la regla de dependencia (el core no importó nada de un cliente).
- [ ] Logging/métricas cubren el nuevo camino.
