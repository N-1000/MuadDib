# MuadDib

Intent router hibrido en cascada (reglas -> embeddings -> LLM) para clasificar
la intencion de cada mensaje y enrutarlo a la accion correspondiente de la
forma mas barata, controlada y auditable posible.

Primera implementacion real: EcoPulse AI (asistente ambiental de la red de
sensores Tangara, Cali). Pensado para extraerse luego como paquete reutilizable
para otros clientes.

Ver `CLAUDE.md` para las reglas de arquitectura y el alcance de la capa
determinista.

## Desarrollo

```
uv sync
uv run pytest
```
