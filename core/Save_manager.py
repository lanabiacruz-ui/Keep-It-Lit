import json
from datetime import datetime
from pathlib import Path


SAVES_DIR = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "saves"
)

SLOTS = ["save_01.json", "save_02.json", "save_03.json"]


EMPTY = "empty"
OK = "ok"
CORRUPT = "corrupt"


def _read_slot(path):

 

    path = Path(path)

    if not path.exists() or path.stat().st_size == 0:
        return EMPTY, {}

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

    except (json.JSONDecodeError, OSError, UnicodeDecodeError):
        return CORRUPT, {}

    if not isinstance(data, dict):
        return CORRUPT, {}

    if not data:
        return EMPTY, {}

    return OK, data


def _slot_is_empty(path):

    status, _ = _read_slot(path)

    return status == EMPTY


def list_slots():

   

    slots = []

    for number, slot in enumerate(SLOTS, start=1):

        path = SAVES_DIR / slot

        status, data = _read_slot(path)

        slots.append({
            "slot": number,
            "path": path,
            "status": status,
            "empty": status == EMPTY,
            "player_name": str(data.get("player_name", "")),
            "created_at": data.get("created_at", ""),
            "last_played": data.get("last_played", ""),
            "data": data,
        })

    return slots


def get_free_slot():



    for slot in SLOTS:

        candidate = SAVES_DIR / slot

        if _slot_is_empty(candidate):
            return candidate

    return None


def create_new_save(player_name):

 

    SAVES_DIR.mkdir(parents=True, exist_ok=True)

    path = get_free_slot()

    if path is None:
        return None

    now = datetime.now().isoformat(timespec="seconds")

    data = {
        "player_name": player_name,
        "created_at": now,
        "last_played": now,
    }

    with open(path, "w", encoding="utf-8") as f:

        json.dump(
            data,
            f,
            indent=4,
            ensure_ascii=False
        )

    return path


def load_save(path):



    status, data = _read_slot(path)

    if status != OK:
        return None

    return data


def save_progress(path, **fields):



    if path is None:
        return False

    status, data = _read_slot(path)

    if status == CORRUPT:
        return False

    data = dict(data)

    data.update(fields)

    data["last_played"] = datetime.now().isoformat(timespec="seconds")

    try:

        with open(path, "w", encoding="utf-8") as f:

            json.dump(
                data,
                f,
                indent=4,
                ensure_ascii=False
            )

    except OSError:
        return False

    return True


def delete_save(path):


    try:

        with open(path, "w", encoding="utf-8"):
            pass

    except OSError:
        return False

    return True