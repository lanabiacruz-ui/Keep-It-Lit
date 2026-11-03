import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SETTINGS_PATH = ROOT / "data" / "settings.json"

SAFE_BELOW = 0.85

_state = {"data": None}


def _read():
    try:
        with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            return data
    except (OSError, ValueError, UnicodeDecodeError):
        pass
    return {}


def _values():
    if _state["data"] is None:
        raw = _read()

        if "flash_level" in raw:
            try:
                level = max(0.0, min(1.0, float(raw["flash_level"])))
            except (TypeError, ValueError):
                level = 1.0
        elif raw.get("flash_safe"):
            level = 0.3
        else:
            level = 1.0

        _state["data"] = {
            "flash_level": level,
            "tutorial_hints": bool(raw.get("tutorial_hints", True)),
            "show_fps": bool(raw.get("show_fps", False)),
        }

    return _state["data"]


def _save(key, value):
    _values()[key] = value

    data = _read()
    data[key] = value

    try:
        SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
    except OSError:
        return False

    return True


def flash_level():
    return _values()["flash_level"]


def flash_safe():
    return _values()["flash_level"] < SAFE_BELOW


def tutorial_hints():
    return _values()["tutorial_hints"]


def show_fps():
    return _values()["show_fps"]


def set_flash_level(value):
    return _save("flash_level", round(max(0.0, min(1.0, float(value))), 3))


def set_tutorial_hints(value):
    return _save("tutorial_hints", bool(value))


def set_show_fps(value):
    return _save("show_fps", bool(value))