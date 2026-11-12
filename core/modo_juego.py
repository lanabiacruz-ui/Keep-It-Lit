"""Interruptor de "todo desbloqueado" (data/modo_juego.json).

    {"todo_desbloqueado": true}
        Tienes TODAS las skins y TODOS los logros, siempre.

    {"todo_desbloqueado": false}
        El juego queda como recien instalado: ajustes (volumen, controles,
        skin elegida, skins compradas, bailes), logros, contadores y
        la historia vuelven a cero, y arranca en PANTALLA COMPLETA.
        Las partidas guardadas (data/saves) NO se tocan.
        El reinicio se hace UNA sola vez al cambiar a false (asi el
        progreso que haga despues no se borra cada vez que abres el juego).

Para volver a reiniciar: pon true, abre el juego una vez, vuelve a poner
false (o borra la linea "_aplicado" del archivo).

La clave "_aplicado" la escribe el juego solo: no la toques.
Si el archivo no existe o esta roto no se cambia nada y no se desbloquea
nada extra.

Este modulo solo usa la libreria estandar: main.py lo llama ANTES de
cargar el resto del juego.
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"

MODO_PATH = DATA / "modo_juego.json"
SETTINGS_PATH = DATA / "settings.json"
ACHIEVEMENTS_PATH = DATA / "achievements.json"
STORY_PATH = DATA / "story.json"

KEY = "todo_desbloqueado"
APPLIED_KEY = "_aplicado"


def _read():

    try:
        with open(MODO_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError, UnicodeDecodeError):
        return None

    if not isinstance(data, dict) or not isinstance(data.get(KEY), bool):
        return None

    return data


_cache = {"stamp": None, "value": False}


def todo_desbloqueado():
    """True solo si el archivo existe y dice true.

    Se llama muchas veces (menus): solo se vuelve a leer si el archivo
    cambio."""

    try:
        stamp = MODO_PATH.stat().st_mtime_ns
    except OSError:
        stamp = None

    if stamp != _cache["stamp"]:

        data = _read()

        _cache["stamp"] = stamp
        _cache["value"] = bool(data and data[KEY])

    return _cache["value"]


def _write_json(path, data):

    try:
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    except OSError:
        return False

    return True


def _reiniciar_todo():
    """Deja todo como recien instalado, menos data/saves."""

    ok = _write_json(SETTINGS_PATH, {"fullscreen": True})

    ok = _write_json(
        ACHIEVEMENTS_PATH, {"unlocked": {}, "counters": {}}
    ) and ok

    ok = _write_json(STORY_PATH, {}) and ok

    return ok


def aplicar_modo():
    """Se llama una vez, al arrancar, antes de cargar el juego."""

    data = _read()

    if data is None:
        return

    value = data[KEY]

    if data.get(APPLIED_KEY) is value:
        return

    if value is False and not _reiniciar_todo():
        return

    data[APPLIED_KEY] = value

    _write_json(MODO_PATH, data)