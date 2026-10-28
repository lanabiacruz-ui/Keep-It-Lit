import json
import time
from pathlib import Path

import pygame

ROOT = Path(__file__).resolve().parent.parent
SOUND_DIRS = (
    ROOT / "assets" / "sounds",
    ROOT / "assets" / "maps" / "sounds",
)
SETTINGS_PATH = ROOT / "data" / "settings.json"

SOUNDS = {
    "coin":        (0.55, 0.04),
    "coin_big":    (0.65, 0.06),
    "pickup":      (0.60, 0.08),
    "gem":         (0.70, 0.10),
    "swing":       (0.45, 0.06),
    "hit":         (0.75, 0.05),
    "hit_heavy":   (0.90, 0.08),
    "hurt":        (0.90, 0.15),
    "enemy_die":   (0.65, 0.05),
    "fireball":    (0.60, 0.08),
    "shot":        (0.40, 0.08),
    "explosion":   (0.90, 0.10),
    "flashbang":   (1.00, 0.30),
    "door_hit":    (0.70, 0.08),
    "door_resist": (0.60, 0.15),
    "door_break":  (0.90, 0.20),
    "chest_open":  (0.80, 0.30),
    "buy":         (0.75, 0.20),
    "wave_clear":  (0.80, 0.50),
    "click":       (0.50, 0.03),
    "light_out":   (0.80, 0.50),
    "alert":       (0.60, 0.50),
    "mosquito":    (0.35, 0.80),
    "ui_confirm":  (0.50, 0.05),
    "ui_back":     (0.50, 0.05),
    "step_a":      (0.30, 0.00),
    "step_b":      (0.30, 0.00),
    "slot":        (0.40, 0.03),
    "light_on":    (0.70, 0.20),
    "drop":        (0.60, 0.08),
    "use_item":    (0.50, 0.08),
    "heal":        (0.75, 0.30),
    "shield_up":   (0.75, 0.30),
    "magnet_on":   (0.55, 0.20),
    "magnet_off":  (0.55, 0.20),
    "msg":         (0.30, 0.30),
    "tick":        (0.55, 0.50),
    "tick_high":   (0.75, 0.50),
    "game_over":   (0.90, 1.00),
    "wave_start":  (0.85, 0.80),
    "achievement": (0.80, 0.50),
    "shop_open":   (0.60, 0.30),
    "shop_close":  (0.50, 0.30),
    "pause_open":  (0.50, 0.20),
    "pause_close": (0.50, 0.20),
    "map_complete": (0.90, 1.00),
    "portal":      (0.70, 0.50),
    "place":       (0.70, 0.15),
    "bite":        (0.70, 0.30),
    "slime_hit":   (0.60, 0.08),
    "crackle":     (0.50, 0.90),
    "deny":          (0.55, 0.15),
    "objective_new":  (0.50, 0.40),
    "objective_done": (0.65, 0.50),
    "tutorial_page":  (0.50, 0.06),
    "heartbeat":      (0.70, 0.70),
    "boss_slam":      (1.00, 0.50),
    "boss_roar":      (0.95, 0.80),
    "talk_a":         (0.30, 0.0),
    "talk_b":         (0.30, 0.0),
    "talk_c":         (0.30, 0.0),
    "talk_d":         (0.30, 0.0),
}


def _saved_sfx_volume():

    try:
        with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)

        return max(0.0, min(1.0, float(data.get("sfx_volume", 0.7))))

    except (OSError, ValueError, TypeError, AttributeError):
        return 0.7


class AudioManager:

    def __init__(self):

        self.enabled = False
        self.volume = _saved_sfx_volume()

        self._sounds = {}
        self._last = {}

        self._init_mixer()


    def _init_mixer(self):

        try:

            if not pygame.mixer.get_init():
                pygame.mixer.init()

            pygame.mixer.set_num_channels(32)

            self.enabled = True

        except pygame.error:

            self.enabled = False

    def _load(self, name):

        if name in self._sounds:
            return self._sounds[name]

        sound = None

        for folder in SOUND_DIRS:

            for ext in (".wav", ".ogg"):

                path = folder / f"{name}{ext}"

                if path.exists():

                    try:
                        sound = pygame.mixer.Sound(str(path))
                    except pygame.error:
                        sound = None

                    break

            if sound is not None:
                break

        if sound is None:
            print(f"[audio] no se encontro el sonido '{name}'")

        self._sounds[name] = sound

        return sound

    def preload(self):

        if not self.enabled:
            return

        for name in SOUNDS:
            self._load(name)


    def play(self, name, volume=1.0):

        if not self.enabled or self.volume <= 0.0:
            return

        base, gap = SOUNDS.get(name, (0.7, 0.05))

        now = time.monotonic()

        if now - self._last.get(name, -10.0) < gap:
            return

        sound = self._load(name)

        if sound is None:
            return

        self._last[name] = now

        sound.set_volume(max(0.0, min(1.0, base * volume * self.volume)))

        sound.play()

    def set_sfx_volume(self, value):

        self.volume = max(0.0, min(1.0, float(value)))

    def stop_all(self):

        if self.enabled:
            pygame.mixer.stop()


audio = AudioManager()