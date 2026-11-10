import json
import math
import random
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
    "chest_win":   (0.85, 0.40),
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
    "tonto_a":        (0.34, 0.0),
    "tonto_b":        (0.34, 0.0),
    "tonto_c":        (0.34, 0.0),
    # voces de los jefes (tools/make_boss_voices.py)
    "golem_a":        (0.55, 0.0),
    "golem_b":        (0.55, 0.0),
    "golem_c":        (0.55, 0.0),
    "golem_thud":     (0.85, 0.15),
    "golem_intro":    (0.95, 0.50),
    "pina_a":         (0.38, 0.0),
    "pina_b":         (0.38, 0.0),
    "pina_c":         (0.38, 0.0),
    "pina_boing":     (0.55, 0.10),
    "pina_intro":     (0.75, 0.50),

    # --- v0.2.1: generados por tools/make_sounds_extra.py ---
    "hit_wood": (0.30, 0.06),
    "hit_squish": (0.25, 0.06),
    "hit_squeak": (0.23, 0.06),
    "hit_stone": (0.37, 0.06),
    "hit_metal": (0.42, 0.06),
    "hit_glass": (0.41, 0.06),
    "hit_pina": (0.31, 0.06),
    "die_wood": (0.49, 0.05),
    "die_bug": (0.60, 0.05),
    "die_stone": (0.41, 0.05),
    "die_metal": (0.56, 0.05),
    "die_pina": (0.48, 0.05),
    "golem_roar": (0.56, 0.8),
    "golem_rock": (0.55, 0.08),
    "golem_wave": (0.67, 0.3),
    "golem_wallhit": (0.75, 0.5),
    "golem_beam_charge": (0.31, 0.8),
    "golem_beam": (0.57, 0.5),
    "golem_sweep": (0.36, 0.5),
    "golem_blast": (0.83, 0.8),
    "golem_summon": (0.42, 0.8),
    "golem_phase": (0.64, 1.0),
    "golem_die": (1.00, 1.5),
    "golem_crack": (0.71, 0.3),
    "pina_bounce": (0.52, 0.12),
    "pina_split": (0.50, 0.4),
    "pina_merge": (0.38, 0.4),
    "pina_summon": (0.57, 0.8),
    "pina_phase": (0.66, 1.0),
    "pina_roar": (0.43, 0.8),
    "pina_die": (0.68, 1.2),
    "pina_crack": (0.66, 0.3),
    "bag_put": (0.28, 0.08),
    "slot_swap": (0.26, 0.05),
    "gulp": (0.31, 0.3),
    "trash": (0.53, 0.1),
    "lift": (0.43, 0.1),
    "feed_fire": (0.29, 0.2),
    "trap_free": (0.47, 0.3),
    "trap_snap": (0.67, 0.4),
    "crusher_warn": (0.38, 0.5),
    "crusher_close": (0.26, 0.3),
    "crusher_thud": (0.55, 0.4),
    "crusher_open": (0.22, 0.5),
    "fire_hit": (0.64, 0.06),
    "fire_hit_heavy": (0.69, 0.1),
    "emote": (0.27, 0.15),
    "chest_fail": (0.39, 0.4),
    "ui_move": (0.15, 0.04),
    "step_c": (0.21, 0.0),
    "step_d": (0.19, 0.0),
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


    def play(self, name, volume=1.0, jitter=0.0):
        """jitter: variacion al azar del volumen (0.1 = +-10%), para que un
        sonido que se repite mucho (pisadas, golpes) no suene mecanico."""

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

        if jitter > 0.0:
            volume *= 1.0 + random.uniform(-jitter, jitter)

        sound.set_volume(max(0.0, min(1.0, base * volume * self.volume)))

        sound.play()

    def play_at(self, name, source, listener, radius=520.0, volume=1.0):
        """Sonido posicional: baja con la distancia entre 'source' y
        'listener' (tuplas x, y) y se corta pasado 'radius'."""

        dx = source[0] - listener[0]
        dy = source[1] - listener[1]

        k = 1.0 - math.hypot(dx, dy) / radius

        if k <= 0.04:
            return

        self.play(name, volume * (k ** 1.3))

    def set_sfx_volume(self, value):

        self.volume = max(0.0, min(1.0, float(value)))

    def stop_all(self):

        if self.enabled:
            pygame.mixer.stop()


audio = AudioManager()