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

# Cada logro puede tener:
#   goal    -> cuanto hay que juntar (1 = se desbloquea de una)
#   counter -> nombre del contador global que lo alimenta (si juntas de a poco)
# Mas adelante cada logro va a regalar una skin de color: cuando toque,
# se agrega un campo "skin" aca y listo.
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
        "desc": "Completá Orkun, la zona 1 (la sala de la derecha)",
        "goal": 1,
    },
    {
        "id": "zona_2",
        "title": "Segunda zona",
        "desc": "Completá Stonun, la zona 2 (la del Guardián, a la izquierda)",
        "goal": 1,
    },
    {
        "id": "perder_50",
        "title": "Mala racha",
        "desc": "Perdé 50 veces",
        "goal": DEFEATS_GOAL,
        "counter": "defeats",
    },

    # ---- logros raros ----
    {
        "id": "ultimo_segundo",
        "title": "Por los pelos",
        "desc": "Conseguí una luz cuando te quedaba menos de 2 s",
        "goal": 1,
    },
    {
        "id": "intocable",
        "title": "Intocable",
        "desc": "Pasá una oleada 5 o más sin recibir un solo golpe",
        "goal": 1,
    },
    {
        "id": "abrazo_golem",
        "title": "Abrazo de oso",
        "desc": "Dejá que un Golem te agarre (y contalo)",
        "goal": 1,
    },
    {
        "id": "ojos_ciegos",
        "title": "¡Mis ojos!",
        "desc": "Recibí la explosión de un Destello en la cara",
        "goal": 1,
    },
    {
        "id": "desactivado",
        "title": "Desactivado",
        "desc": "Derrotá a un Destello antes de que te explote",
        "goal": 1,
    },
    {
        "id": "slime_brillante",
        "title": "Cacería de oro",
        "desc": "Atrapá un Slime Brillante",
        "goal": 1,
    },
    {
        "id": "gelatinero",
        "title": "Gelatinero",
        "desc": "Derrotá 25 slimes",
        "goal": 25,
        "counter": "slimes",
    },
    {
        "id": "entomologo",
        "title": "Naturalista",
        "desc": "Descubrí a todas las criaturas de la enciclopedia",
        "goal": 1,
    },
    {
        "id": "exterminador",
        "title": "Exterminador",
        "desc": "Derrotá 200 enemigos",
        "goal": 200,
        "counter": "kills",
    },
    {
        "id": "saqueador",
        "title": "Saqueador",
        "desc": "Abrí 25 cofres",
        "goal": 25,
        "counter": "chests",
    },
    {
        "id": "pirotecnico",
        "title": "Pirotécnico",
        "desc": "Lanzá 100 bolas de fuego",
        "goal": 100,
        "counter": "fireballs",
    },
    {
        "id": "derribapuertas",
        "title": "Derribapuertas",
        "desc": "Rompé 10 puertas",
        "goal": 10,
        "counter": "doors",
    },
    {
        "id": "dragon_monedas",
        "title": "Dragón de monedas",
        "desc": "Tené 500 monedas al mismo tiempo",
        "goal": 1,
    },
    {
        "id": "coctel",
        "title": "Cóctel molotov",
        "desc": "Tené 3 efectos de objetos activos a la vez",
        "goal": 1,
    },
    {
        "id": "sin_red",
        "title": "Sin red",
        "desc": "Completá una zona en modo Hardcore",
        "goal": 1,
    },
]

_IDS = {a["id"] for a in ACHIEVEMENTS}

# contador -> logros que alimenta
_COUNTERS = {}

for _ach in ACHIEVEMENTS:

    if _ach.get("counter"):
        _COUNTERS.setdefault(_ach["counter"], []).append(_ach)


class AchievementManager:

    def __init__(self):

        self.unlocked = {}
        self.counters = {}
        self.pending = []

        self.load()

    # "defeats" se llamaba asi en la version anterior del archivo
    @property
    def defeats(self):

        return self.counters.get("defeats", 0)

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

        self.counters = {}

        raw_counters = data.get("counters", {})

        if isinstance(raw_counters, dict):

            for key, value in raw_counters.items():

                if key in _COUNTERS:

                    try:
                        self.counters[key] = max(0, int(value))
                    except (TypeError, ValueError):
                        pass

        # archivos viejos guardaban las derrotas aparte
        if "defeats" not in self.counters:

            try:
                self.counters["defeats"] = max(
                    0, int(data.get("defeats", 0))
                )
            except (TypeError, ValueError):
                self.counters["defeats"] = 0

    def save(self):

        data = {
            "unlocked": dict(self.unlocked),
            "counters": dict(self.counters),
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

    def add_counter(self, name, amount=1, save=True):
        """Suma al contador global y desbloquea los logros que lo usan."""

        if name not in _COUNTERS or amount <= 0:
            return

        total = self.counters.get(name, 0) + int(amount)

        self.counters[name] = total

        for ach in _COUNTERS[name]:

            if total >= ach["goal"]:
                self.unlock(ach["id"])

        if save:
            self.save()

    def add_defeat(self):

        self.add_counter("defeats")

    def progress(self, achievement_id):

        for ach in ACHIEVEMENTS:

            if ach["id"] != achievement_id:
                continue

            if achievement_id in self.unlocked:
                return ach["goal"]

            counter = ach.get("counter")

            if counter:
                return min(self.counters.get(counter, 0), ach["goal"])

            return 0

        return 0

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