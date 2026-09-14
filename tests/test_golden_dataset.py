import json
from pathlib import Path

import pytest

from intent_router.rules import analizar

_RUTA_DATASET = Path(__file__).parent.parent / "golden_dataset.json"
_DATASET = json.loads(_RUTA_DATASET.read_text(encoding="utf-8"))


def _parametros():
    for entrada in _DATASET:
        marcas = ()
        if entrada["gap_conocido"] is not None:
            marcas = (pytest.mark.xfail(reason=entrada["gap_conocido"], strict=True),)
        yield pytest.param(entrada, id=entrada["mensaje"], marks=marcas)


@pytest.mark.parametrize("entrada", list(_parametros()))
def test_golden_dataset(entrada):
    resultado = analizar(entrada["mensaje"])
    verbos = [clausula.verbo for clausula in resultado.clausulas]
    assert verbos == entrada["verbos_esperados"]
    assert resultado.senales.tiene_conector == entrada["tiene_conector_esperado"]
    assert resultado.senales.tiene_negacion == entrada["tiene_negacion_esperada"]
