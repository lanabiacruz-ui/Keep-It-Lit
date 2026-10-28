import json
from pathlib import Path

import pygame

ROOT = Path(__file__).resolve().parent.parent
MUSIC_DIRS = (
    ROOT / "assets" / "music",
    ROOT / "assets" / "maps" / "sounds",
)
SETTINGS_PATH = ROOT / "data" / "settings.json"

TRACKS = {
    "menu": {"fade_in": 3.0, "fade_out": 2.0, "gain": 1.0},
    "ambiente": {"fade_in": 5.0, "fade_out": 2.5, "gain": 1.0},
    "combate": {"fade_in": 0.9, "fade_out": 2.0, "gain": 1.0},
    "jefe": {"fade_in": 0.6, "fade_out": 1.2, "gain": 1.0},
}


def _saved_music_volume():

    try:
        with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)

        return max(0.0, min(1.0, float(data.get("music_volume", 0.7))))

    except (OSError, ValueError, TypeError, AttributeError):
        return 0.7


class MusicManager:

    def __init__(self):

        self.enabled = False
        self.volume = _saved_music_volume()

        self.current = None
        self.target = None
        self.fade = 0.0

        self._hold = 0.0
        self._stingers = {}

        self._init_mixer()

    def _init_mixer(self):

        try:

            if not pygame.mixer.get_init():
                pygame.mixer.init()

            self.enabled = True

        except pygame.error:

            self.enabled = False

    def _path(self, name):

        for folder in MUSIC_DIRS:

            for ext in (".ogg", ".wav", ".mp3"):

                path = folder / f"{name}{ext}"

                if path.exists():
                    return path

        return None

    def _start(self, name):

        path = self._path(name)

        if path is None:
            print(f"[musica] no se encontro la pista '{name}'")
            self.current = None
            self.target = None
            return

        try:
            pygame.mixer.music.load(str(path))
            pygame.mixer.music.set_volume(0.0)
            pygame.mixer.music.play(-1)
            self.current = name
            self.fade = 0.0

        except pygame.error:
            print(f"[musica] no se pudo reproducir '{name}'")
            self.current = None
            self.target = None

    def play(self, name):

        if name is not None and name not in TRACKS:
            return

        self.target = name

    def stop(self):

        self.target = None

    def stinger(self, name, hold=0.0):

        if not self.enabled:
            return

        sound = self._stingers.get(name)

        if sound is None:

            path = self._path(name)

            if path is None:
                print(f"[musica] no se encontro el sonido '{name}'")
                return

            try:
                sound = pygame.mixer.Sound(str(path))
            except pygame.error:
                return

            self._stingers[name] = sound

        sound.set_volume(self.volume)
        sound.play()

        self._hold = max(self._hold, hold)

    def set_volume(self, value):

        self.volume = max(0.0, min(1.0, float(value)))

        self._apply_volume()

    def _apply_volume(self):

        if not self.enabled or self.current is None:
            return

        gain = TRACKS[self.current]["gain"]

        pygame.mixer.music.set_volume(
            max(0.0, min(1.0, self.volume * gain * self.fade))
        )

    def update(self, dt):

        if not self.enabled:
            return

        if self._hold > 0.0:
            self._hold = max(0.0, self._hold - dt)

        if self.current != self.target:

            if self.current is None:

                if self._hold <= 0.0:
                    self._start(self.target)

            else:

                out = TRACKS[self.current]["fade_out"]

                self.fade -= dt / out

                if self.fade <= 0.0:

                    self.fade = 0.0

                    pygame.mixer.music.stop()

                    self.current = None

                    if self.target is not None:
                        self._start(self.target)

        elif self.current is not None and self.fade < 1.0:

            self.fade = min(
                1.0, self.fade + dt / TRACKS[self.current]["fade_in"]
            )

        self._apply_volume()


music = MusicManager()