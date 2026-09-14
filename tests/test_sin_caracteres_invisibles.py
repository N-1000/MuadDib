import subprocess
import unicodedata
from pathlib import Path

_CATEGORIAS_PROHIBIDAS = {"Mn", "Cf", "Co"}
_RAIZ = Path(__file__).resolve().parent.parent


def _archivos_trackeados() -> list[Path]:
    resultado = subprocess.run(
        ["git", "ls-files", "*.py", "*.yaml", "*.yml", "*.txt", "*.md"],
        cwd=_RAIZ,
        capture_output=True,
        text=True,
        check=True,
    )
    return [_RAIZ / linea for linea in resultado.stdout.splitlines()]


def _caracteres_prohibidos(ruta: Path) -> list[tuple[int, str, str]]:
    texto = ruta.read_text(encoding="utf-8")
    return [
        (indice, hex(ord(caracter)), unicodedata.category(caracter))
        for indice, caracter in enumerate(texto)
        if unicodedata.category(caracter) in _CATEGORIAS_PROHIBIDAS
    ]


def test_sin_caracteres_invisibles_literales_en_el_repo():
    # Una secuencia de escape Unicode es texto ASCII plano al leer el
    # archivo: solo un caracter Mn/Cf/Co real y embebido dispara esto,
    # nunca su representacion como escape. Ver CLAUDE.md, Caracteres no
    # imprimibles.
    hallazgos = {
        str(ruta.relative_to(_RAIZ)): prohibidos
        for ruta in _archivos_trackeados()
        if ruta.exists() and (prohibidos := _caracteres_prohibidos(ruta))
    }
    assert not hallazgos, f"caracteres Mn/Cf/Co literales encontrados: {hallazgos}"
