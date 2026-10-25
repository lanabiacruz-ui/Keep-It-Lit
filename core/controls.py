import json
from pathlib import Path

import pygame


SETTINGS_PATH = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "settings.json"
)

GROUPS = [
    (
        "Movimiento",
        [
            ("up", "Arriba"),
            ("down", "Abajo"),
            ("left", "Izquierda"),
            ("right", "Derecha"),
        ],
    ),
    (
        "Acciones",
        [
            ("pickup", "Recoger"),
            ("drop", "Soltar"),
            ("use", "Usar / Tienda"),
            ("magnet", "Imán"),
            ("attack_mode", "Modo de ataque"),
        ],
    ),
    (
        "Inventario",
        [
            ("slot1", "Casillero 1"),
            ("slot2", "Casillero 2"),
            ("slot3", "Casillero 3"),
            ("slot4", "Casillero 4"),
            ("equipped", "Luz equipada"),
        ],
    ),
]

DEFAULTS = {
    "up": pygame.K_w,
    "down": pygame.K_s,
    "left": pygame.K_a,
    "right": pygame.K_d,
    "pickup": pygame.K_e,
    "drop": pygame.K_q,
    "use": pygame.K_f,
    "magnet": pygame.K_o,
    "attack_mode": pygame.K_g,
    "slot1": pygame.K_1,
    "slot2": pygame.K_2,
    "slot3": pygame.K_3,
    "slot4": pygame.K_4,
    "equipped": pygame.K_5,
}

SLOT_ACTIONS = ("slot1", "slot2", "slot3", "slot4")

FIXED_KEYS = {
    pygame.K_UP,
    pygame.K_DOWN,
    pygame.K_LEFT,
    pygame.K_RIGHT,
    pygame.K_ESCAPE,
    pygame.K_TAB,
    pygame.K_RETURN,
    pygame.K_KP_ENTER,
    pygame.K_F1,
    pygame.K_F2,
    pygame.K_F3,
    pygame.K_F4,
    pygame.K_F5,
    pygame.K_F6,
    pygame.K_F7,
    pygame.K_F8,
    pygame.K_F9,
    pygame.K_F10,
    pygame.K_F11,
    pygame.K_F12,
}

KEY_NAMES = {
    pygame.K_SPACE: "ESPACIO",
    pygame.K_LSHIFT: "SHIFT IZQ",
    pygame.K_RSHIFT: "SHIFT DER",
    pygame.K_LCTRL: "CTRL IZQ",
    pygame.K_RCTRL: "CTRL DER",
    pygame.K_LALT: "ALT IZQ",
    pygame.K_RALT: "ALT DER",
    pygame.K_BACKSPACE: "RETROCESO",
    pygame.K_CAPSLOCK: "BLOQ MAYUS",
    pygame.K_DELETE: "SUPR",
    pygame.K_INSERT: "INSERT",
    pygame.K_HOME: "INICIO",
    pygame.K_END: "FIN",
    pygame.K_PAGEUP: "RE PAG",
    pygame.K_PAGEDOWN: "AV PAG",
}


def key_label(code):

    if code in KEY_NAMES:
        return KEY_NAMES[code]

    try:
        name = pygame.key.name(code)
    except (pygame.error, TypeError, ValueError):
        name = ""

    if not name:
        return "?"

    return name.upper()


class Controls:

    def __init__(self):

        self.keys = dict(DEFAULTS)

        self.load()

    def load(self):

        self.keys = dict(DEFAULTS)

        try:
            with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)

            saved = data.get("controls")

        except (OSError, ValueError, AttributeError, UnicodeDecodeError):
            return

        if not isinstance(saved, dict):
            return

        loaded = dict(DEFAULTS)

        for action in DEFAULTS:

            value = saved.get(action)

            if isinstance(value, int) and not isinstance(value, bool):

                if value > 0 and value not in FIXED_KEYS:
                    loaded[action] = value

        if len(set(loaded.values())) != len(loaded):
            return

        self.keys = loaded

    def save(self):

        data = {}

        try:
            with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)

            if not isinstance(data, dict):
                data = {}

        except (OSError, ValueError, UnicodeDecodeError):
            data = {}

        data["controls"] = {
            action: int(code)
            for action, code in self.keys.items()
        }

        try:
            SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)

            with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)

        except OSError:
            return False

        return True

    def key(self, action):

        return self.keys.get(action, DEFAULTS.get(action))

    def label(self, action):

        return key_label(self.key(action))

    def matches(self, action, key):

        return self.key(action) == key

    def pressed(self, action, pressed_keys):

        return bool(pressed_keys[self.key(action)])

    def action_for(self, key):

        for action, code in self.keys.items():

            if code == key:
                return action

        return None

    def slot_for(self, key):

        for index, action in enumerate(SLOT_ACTIONS):

            if self.keys[action] == key:
                return index

        return None

    def is_reserved(self, key):

        return key in FIXED_KEYS

    def rebind(self, action, key):

        if action not in self.keys or key in FIXED_KEYS:
            return False, None

        if self.keys[action] == key:
            return True, None

        swapped = None

        other = self.action_for(key)

        if other is not None:

            self.keys[other] = self.keys[action]

            swapped = other

        self.keys[action] = key

        self.save()

        return True, swapped

    def reset(self):

        self.keys = dict(DEFAULTS)

        self.save()


controls = Controls()