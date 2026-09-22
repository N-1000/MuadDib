import importlib

import pytest

SCRIPTS_RAIZ = ["validate_canonical", "eval_corpus_baseline", "simulate_cascade"]


@pytest.mark.parametrize("nombre_modulo", SCRIPTS_RAIZ)
def test_script_importa_sin_explotar(nombre_modulo):
    """SentenceTransformer usado como type hint sin importar ya rompio dos de estos scripts con NameError al definir la funcion; nadie se enteraba hasta correrlos a mano."""
    importlib.import_module(nombre_modulo)
