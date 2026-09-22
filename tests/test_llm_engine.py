import asyncio
import time
from types import SimpleNamespace

import anthropic
from intent_router.llm_engine import escalar, resolver_escaladas
from intent_router.router import Decision, RoutingResult
from intent_router.tools import Herramienta


def _config() -> dict:
    return {
        "nivel2": {
            "timeout_s": 8.0,
            "max_vueltas_tool_use": 3,
            "max_tokens_respuesta": 1024,
            "max_caracteres_resultado_herramienta": 50,
            "modelo": "claude-sonnet-5",
        }
    }


def _decision_escalada(
    clausula: str = "mostrame el aire en pance",
    candidato: str | None = "consultar_calidad_aire",
    motivos: tuple[str, ...] = ("confianza_insuficiente",),
    sensitive: bool = False,
) -> Decision:
    return Decision(
        intencion=None,
        nivel=2,
        confianza=0.5,
        accion=("escalate_to_llm",),
        sensitive=sensitive,
        clausula=clausula,
        motivos_escalada=motivos,
        candidato_descartado=candidato,
    )


def _herramienta(name: str, funcion=None, efecto_real: bool = False) -> Herramienta:
    return Herramienta(
        name=name,
        description=f"descripcion de {name}",
        parametros={"type": "object", "properties": {"region": {"type": "string"}}, "required": ["region"]},
        funcion=funcion or (lambda region: f"aire de {region}: bueno"),
        efecto_real=efecto_real,
    )


def _texto(texto: str) -> SimpleNamespace:
    return SimpleNamespace(type="text", text=texto)


def _tool_use(id_: str, name: str, input_: dict) -> SimpleNamespace:
    return SimpleNamespace(type="tool_use", id=id_, name=name, input=input_)


def _respuesta(bloques: list, tokens_in: int = 10, tokens_out: int = 5) -> SimpleNamespace:
    return SimpleNamespace(content=bloques, usage=SimpleNamespace(input_tokens=tokens_in, output_tokens=tokens_out))


class _ClienteFake:
    def __init__(self, respuestas=None, excepcion=None):
        self._respuestas = list(respuestas or [])
        self._excepcion = excepcion
        self.llamadas: list[dict] = []
        self.messages = SimpleNamespace(create=self._create)

    async def _create(self, **kwargs):
        llamada = dict(kwargs)
        llamada["messages"] = list(kwargs["messages"])
        self.llamadas.append(llamada)
        if self._excepcion is not None:
            raise self._excepcion
        return self._respuestas.pop(0)


async def test_escalar_sin_api_key_no_toca_el_cliente():
    cliente = _ClienteFake()
    decision = await escalar((_decision_escalada(),), (), _config(), api_key=None, cliente=cliente)

    assert decision.nivel == 2
    assert decision.accion == ("fallback_seguro",)
    assert "api_key_ausente" in decision.motivos_escalada
    assert cliente.llamadas == []


async def test_escalar_happy_path_ejecuta_herramienta_y_responde():
    respuestas = [
        _respuesta([_tool_use("t1", "show_air", {"region": "pance"})]),
        _respuesta([_texto("El aire en pance esta bien.")]),
    ]
    cliente = _ClienteFake(respuestas)
    herramientas = (_herramienta("show_air"),)

    decision = await escalar((_decision_escalada(),), herramientas, _config(), api_key="x", cliente=cliente)

    assert decision.herramientas_llamadas == ("show_air",)
    assert decision.herramientas_fallidas == ()
    assert decision.respuesta_texto == "El aire en pance esta bien."
    assert decision.respuesta_fundamentada is True
    assert decision.accion == ()
    assert decision.tokens_entrada == 20
    assert decision.tokens_salida == 10
    assert len(cliente.llamadas) == 2


async def test_escalar_herramienta_con_efecto_no_se_ejecuta():
    llamada_funcion = []

    def _enviar_alerta(region):
        llamada_funcion.append(region)
        return "enviada"

    respuestas = [_respuesta([_tool_use("t1", "send_alert", {"region": "pance"})])]
    cliente = _ClienteFake(respuestas)
    herramientas = (_herramienta("send_alert", funcion=_enviar_alerta, efecto_real=True),)

    decision = await escalar((_decision_escalada(),), herramientas, _config(), api_key="x", cliente=cliente)

    assert llamada_funcion == []
    assert decision.herramienta_pendiente == {"name": "send_alert", "input": {"region": "pance"}}
    assert "herramienta_efecto_real_requiere_confirmacion" in decision.motivos_escalada
    assert decision.herramientas_llamadas == ()


async def test_escalar_timeout_devuelve_fallback_seguro():
    cliente = _ClienteFake(excepcion=anthropic.APITimeoutError(request=None))
    decision = await escalar((_decision_escalada(),), (), _config(), api_key="x", cliente=cliente)

    assert decision.accion == ("fallback_seguro",)
    assert "timeout_llm" in decision.motivos_escalada


async def test_escalar_api_error_devuelve_fallback_seguro():
    cliente = _ClienteFake(
        excepcion=anthropic.APIConnectionError(request=None)
    )
    decision = await escalar((_decision_escalada(),), (), _config(), api_key="x", cliente=cliente)

    assert decision.accion == ("fallback_seguro",)
    assert "error_llm" in decision.motivos_escalada


async def test_escalar_limite_de_vueltas_devuelve_fallback_seguro():
    respuestas = [
        _respuesta([_tool_use(f"t{i}", "show_air", {"region": "pance"})]) for i in range(10)
    ]
    cliente = _ClienteFake(respuestas)
    herramientas = (_herramienta("show_air"),)

    decision = await escalar((_decision_escalada(),), herramientas, _config(), api_key="x", cliente=cliente)

    assert decision.accion == ("fallback_seguro",)
    assert "limite_vueltas_tool_use_alcanzado" in decision.motivos_escalada
    assert len(cliente.llamadas) == _config()["nivel2"]["max_vueltas_tool_use"]


async def test_escalar_herramienta_que_tira_excepcion_cuenta_como_fallida():
    def _rompe(region):
        raise RuntimeError("bug interno")

    respuestas = [
        _respuesta([_tool_use("t1", "show_air", {"region": "pance"})]),
        _respuesta([_texto("no tengo ese dato")]),
    ]
    cliente = _ClienteFake(respuestas)
    herramientas = (_herramienta("show_air", funcion=_rompe),)

    decision = await escalar((_decision_escalada(),), herramientas, _config(), api_key="x", cliente=cliente)

    assert decision.herramientas_fallidas == ("show_air",)
    assert decision.herramientas_llamadas == ()
    assert decision.respuesta_fundamentada is False

    segundo_llamado = cliente.llamadas[1]
    tool_result = segundo_llamado["messages"][-1]["content"][0]
    assert tool_result["is_error"] is True
    assert "bug interno" not in tool_result["content"]


async def test_escalar_input_invalido_cuenta_como_fallida_sin_llamar_la_funcion():
    llamada_funcion = []

    def _show_air(**kwargs):
        llamada_funcion.append(kwargs)
        return "ok"

    respuestas = [
        _respuesta([_tool_use("t1", "show_air", {"region": "pance", "extra": "inyeccion"})]),
        _respuesta([_texto("no tengo ese dato")]),
    ]
    cliente = _ClienteFake(respuestas)
    herramientas = (_herramienta("show_air", funcion=_show_air),)

    decision = await escalar((_decision_escalada(),), herramientas, _config(), api_key="x", cliente=cliente)

    assert llamada_funcion == []
    assert decision.herramientas_fallidas == ("show_air",)


async def test_escalar_trunca_resultado_de_herramienta():
    resultado_largo = "x" * 200
    respuestas = [
        _respuesta([_tool_use("t1", "show_air", {"region": "pance"})]),
        _respuesta([_texto("listo")]),
    ]
    cliente = _ClienteFake(respuestas)
    herramientas = (_herramienta("show_air", funcion=lambda region: resultado_largo),)

    await escalar((_decision_escalada(),), herramientas, _config(), api_key="x", cliente=cliente)

    tope = _config()["nivel2"]["max_caracteres_resultado_herramienta"]
    segundo_llamado = cliente.llamadas[1]
    tool_result = segundo_llamado["messages"][-1]["content"][0]
    assert len(tool_result["content"]) <= tope + len("... [truncado]")
    assert tool_result["content"].endswith("... [truncado]")


async def test_escalar_junta_clausulas_de_un_mismo_mensaje_en_una_conversacion():
    respuestas = [_respuesta([_texto("resuelto")])]
    cliente = _ClienteFake(respuestas)

    d1 = _decision_escalada(clausula="mostrame el aire", candidato="consultar_calidad_aire")
    d2 = _decision_escalada(clausula="cancela mi alerta", candidato="cancelar_alerta", sensitive=True)

    decision = await escalar((d1, d2), (), _config(), api_key="x", cliente=cliente)

    assert len(cliente.llamadas) == 1
    assert "mostrame el aire" in decision.clausula
    assert "cancela mi alerta" in decision.clausula
    assert decision.sensitive is True
    assert decision.candidato_descartado is None


async def test_resolver_escaladas_sin_decisiones_nivel2_no_llama_al_engine():
    cliente = _ClienteFake()
    resultado = RoutingResult(
        mensaje="hola",
        decisiones=(Decision(intencion="saludo", nivel=0, confianza=1.0, accion=("reply",), sensitive=False),),
    )

    salida = await resolver_escaladas(resultado, (), _config(), api_key="x", cliente=cliente)

    assert salida is resultado
    assert cliente.llamadas == []


async def test_resolver_escaladas_reemplaza_solo_las_decisiones_escaladas():
    respuestas = [_respuesta([_texto("resuelto")])]
    cliente = _ClienteFake(respuestas)
    decision_n0 = Decision(intencion="saludo", nivel=0, confianza=1.0, accion=("reply",), sensitive=False)
    resultado = RoutingResult(mensaje="hola, mostrame el aire", decisiones=(decision_n0, _decision_escalada()))

    salida = await resolver_escaladas(resultado, (), _config(), api_key="x", cliente=cliente)

    assert len(salida.decisiones) == 2
    assert salida.decisiones[0] == decision_n0
    assert salida.decisiones[1].nivel == 2
    assert salida.decisiones[1].respuesta_texto == "resuelto"


async def test_escalar_corre_herramienta_sincrona_en_thread_sin_bloquear_el_loop():
    def _dormir(region):
        time.sleep(0.2)
        return "listo"

    respuestas = [
        _respuesta([_tool_use("t1", "show_air", {"region": "pance"})]),
        _respuesta([_texto("hecho")]),
    ]
    cliente = _ClienteFake(respuestas)
    herramientas = (_herramienta("show_air", funcion=_dormir),)

    async def _tarea_paralela():
        for _ in range(10):
            await asyncio.sleep(0.02)

    inicio = time.perf_counter()
    await asyncio.gather(
        escalar((_decision_escalada(),), herramientas, _config(), api_key="x", cliente=cliente),
        _tarea_paralela(),
    )
    duracion = time.perf_counter() - inicio

    assert duracion < 0.35


async def test_escalar_soporta_herramienta_async_sin_pasarla_por_un_thread():
    llamadas = []

    async def _consulta_async(region):
        llamadas.append(region)
        await asyncio.sleep(0.01)
        return "async ok"

    respuestas = [
        _respuesta([_tool_use("t1", "show_air", {"region": "pance"})]),
        _respuesta([_texto("hecho")]),
    ]
    cliente = _ClienteFake(respuestas)
    herramientas = (_herramienta("show_air", funcion=_consulta_async),)

    decision = await escalar((_decision_escalada(),), herramientas, _config(), api_key="x", cliente=cliente)

    assert llamadas == ["pance"]
    assert decision.herramientas_llamadas == ("show_air",)
