"""Interruptor de los trucos (teclas F5 a F9).

Se prende o apaga desde data/trucos.json:

    {"trucos": true}     -> F5-F9 funcionan
    {"trucos": false}    -> F5-F9 no hacen nada

F3 y F4 NO son trucos (son para el jugador) y andan siempre.
Si el archivo no existe o esta roto, los trucos quedan apagados.
El archivo se lee en cada pulsacion, asi que se puede cambiar
con el juego abierto.
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TRUCOS_PATH = ROOT / "data" / "trucos.json"


def trucos_activados():

    try:
        with open(TRUCOS_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError, UnicodeDecodeError):
        return False

    return isinstance(data, dict) and data.get("trucos") is True