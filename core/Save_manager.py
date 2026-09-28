import json
from datetime import datetime
from pathlib import Path


SAVES_DIR = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "saves"
)

SLOTS = ["save_01.json", "save_02.json", "save_03.json"]


def _slot_is_empty(path):

    
    if not path.exists() or path.stat().st_size == 0:
        return True

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

    except (json.JSONDecodeError, OSError):
        
        return False

    return not data


def create_new_save(player_name):

    SAVES_DIR.mkdir(parents=True, exist_ok=True)

    path = SAVES_DIR / SLOTS[0]

    for slot in SLOTS:

        candidate = SAVES_DIR / slot

        if _slot_is_empty(candidate):

            path = candidate
            break

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
