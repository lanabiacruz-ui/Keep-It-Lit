import json
from datetime import datetime
from pathlib import Path

from core.audio_manager import audio


ACHIEVEMENTS_PATH = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "achievements.json"
)

DEFEATS_GOAL = 50

ACHIEVEMENTS = [
    {
        "id": "region_1",
        "title": "Primera región",
        "desc": "Pasá la primera región y llegá al segundo mapa",
        "goal": 1,
    },
    {
        "id": "zona_1",
        "title": "Primera zona",
        "desc": "Completá Orkun - Sala de combate 1 (la de la derecha)",
        "goal": 1,
    },
    {
        "id": "zona_2",
        "title": "Segunda zona",
        "desc": "Completá Orkun - Sala de combate 2 (la del Guardián, a la izquierda)",
        "goal": 1,
    },
    {
        "id": "perder_50",
        "title": "Mala racha",
        "desc": "Perdé 50 veces",
        "goal": DEFEATS_GOAL,
    },
]

_IDS = {a["id"] for a in ACHIEVEMENTS}


class AchievementManager:

    def __init__(self):

        self.unlocked = {}
        self.defeats = 0
        self.pending = []

        self.load()

    def load(self):

        data = {}

        try:
            with open(ACHIEVEMENTS_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)

        except (OSError, ValueError):
            data = {}

        if not isinstance(data, dict):
            data = {}

        raw = data.get("unlocked", {})

        self.unlocked = {}

        if isinstance(raw, dict):

            for key, value in raw.items():

                if key in _IDS:
                    self.unlocked[key] = str(value)

        try:
            self.defeats = max(0, int(data.get("defeats", 0)))
        except (TypeError, ValueError):
            self.defeats = 0

    def save(self):

        data = {
            "unlocked": dict(self.unlocked),
            "defeats": self.defeats,
        }

        try:

            ACHIEVEMENTS_PATH.parent.mkdir(parents=True, exist_ok=True)

            with open(ACHIEVEMENTS_PATH, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)

        except OSError:
            return False

        return True

    def is_unlocked(self, achievement_id):

        return achievement_id in self.unlocked

    def unlock(self, achievement_id):

        if achievement_id not in _IDS:
            return False

        if achievement_id in self.unlocked:
            return False

        self.unlocked[achievement_id] = datetime.now().isoformat(
            timespec="seconds"
        )

        self.pending.append(achievement_id)

        self.save()

        audio.play("achievement")

        return True

    def add_defeat(self):

        self.defeats += 1

        if self.defeats >= DEFEATS_GOAL:
            self.unlock("perder_50")

        self.save()

    def progress(self, achievement_id):

        if achievement_id == "perder_50":
            return min(self.defeats, DEFEATS_GOAL)

        return 1 if achievement_id in self.unlocked else 0

    def rows(self):

        rows = []

        for ach in ACHIEVEMENTS:

            row = dict(ach)

            row["unlocked"] = ach["id"] in self.unlocked
            row["progress"] = self.progress(ach["id"])

            rows.append(row)

        return rows

    def title_of(self, achievement_id):

        for ach in ACHIEVEMENTS:

            if ach["id"] == achievement_id:
                return ach["title"]

        return ""

    def take_pending(self):

        pending = self.pending

        self.pending = []

        return pending


achievements = AchievementManager()