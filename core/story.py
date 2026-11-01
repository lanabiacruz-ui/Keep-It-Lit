import json
from pathlib import Path


_PATH = Path(__file__).resolve().parent.parent / "data" / "story.json"

_state = None


def _load():

    global _state

    if _state is not None:
        return _state

    _state = {}

    try:

        with open(_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)

        if isinstance(data, dict):
            _state = data

    except (OSError, ValueError):
        pass

    return _state


def _save():

    try:

        _PATH.parent.mkdir(parents=True, exist_ok=True)

        with open(_PATH, "w", encoding="utf-8") as f:
            json.dump(_state, f, indent=4)

    except OSError:
        pass


def cat_gone():
    """True despues de que el comic muestra que el gato ya no esta."""

    return bool(_load().get("cat_gone", False))


def set_cat_gone():

    state = _load()

    if state.get("cat_gone"):
        return

    state["cat_gone"] = True

    _save()