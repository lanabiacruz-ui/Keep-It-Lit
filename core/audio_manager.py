"""Efectos de sonido del juego.

Uso desde cualquier archivo:

    from core.audio_manager import audio

    audio.play("coin")

Los sonidos estan en assets/sounds/*.wav (se generan con
tools/make_sounds.py; se pueden reemplazar por cualquier .wav u .ogg con
el mismo nombre). Si no hay placa de sonido o falta un archivo, no pasa
nada: simplemente no suena.

El volumen sale de "Efectos" en Configuraciones (sfx_volume).
"""

import json
import time
from pathlib import Path

import pygame

ROOT = Path(__file__).resolve().parent.parent
SOUND_DIR = ROOT / "assets" / "sounds"
SETTINGS_PATH = ROOT / "data" / "settings.json"

# nombre -> (volumen propio 0..1, espera minima entre dos sonidos iguales
# en segundos). La espera evita que 30 enemigos tapen todo con el mismo
# sonido a la vez.
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

    # ---------- arranque ----------

    def _init_mixer(self):

        try:

            if not pygame.mixer.get_init():
                pygame.mixer.init()

            pygame.mixer.set_num_channels(32)

            self.enabled = True

        except pygame.error:

            # Sin placa de sonido: el juego sigue andando, sin audio
            self.enabled = False

    def _load(self, name):

        if name in self._sounds:
            return self._sounds[name]

        sound = None

        for ext in (".wav", ".ogg"):

            path = SOUND_DIR / f"{name}{ext}"

            if path.exists():

                try:
                    sound = pygame.mixer.Sound(str(path))
                except pygame.error:
                    sound = None

                break

        self._sounds[name] = sound

        return sound

    def preload(self):
        """Carga todos los sonidos de una (se llama al abrir el juego,
        asi el primer golpe no tiene un tironcito)."""

        if not self.enabled:
            return

        for name in SOUNDS:
            self._load(name)

    # ---------- uso ----------

    def play(self, name, volume=1.0):
        """Reproduce un efecto. No hace nada si no hay audio."""

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
        """Cambia el volumen de los efectos (0.0 a 1.0)."""

        self.volume = max(0.0, min(1.0, float(value)))

    def stop_all(self):

        if self.enabled:
            pygame.mixer.stop()


# Una sola instancia para todo el juego
audio = AudioManager()