import math

from core.audio_manager import audio

STEP_INTERVAL = 0.34
CRACKLE_INTERVAL = 1.15
CRACKLE_RANGE = 420.0
HEART_INTERVAL = 0.95
HEART_LIFE = 0.2

DENY_PREFIXES = (
    "no te alcanzan",
    "inventario lleno",
    "eso no se puede",
    "necesitas una luz",
    "faltan ",
)


def _hud_total(game):

    counts = getattr(game.hud, "counts", None) or []

    return sum(int(c) for c in counts if c)


def _attached_total(game):

    total = 0

    for arena in getattr(game, "arenas", []):

        for enemy in getattr(arena, "enemies", []):

            if getattr(enemy, "attached", False):
                total += 1

    return total


class SoundWatcher:

    def __init__(self):

        self.game = None
        self.prev = None
        self.step_t = 0.0
        self.step_flip = False
        self.crackle_t = 0.0
        self.slime_flash = {}
        self.broken = False
        self.heart_t = 0.0
        self.disabled = set()

    def _read(self, game):

        return {
            "slot": game.selected_slot,
            "has_match": bool(game.has_match),
            "magnet": bool(game.magnet_mode),
            "msg_t": float(getattr(game, "message_timer", 0.0) or 0.0),
            "msg_text": str(getattr(game, "message", "") or ""),
            "obj_phase": getattr(
                getattr(game, "objectives", None), "phase", None
            ),
            "obj_index": getattr(
                getattr(game, "objectives", None), "index", None
            ),
            "tut_index": getattr(
                getattr(game, "tutorial", None), "index", None
            ),
            "state": game.state,
            "pause": game.pause_view,
            "shop": game.shop is not None,
            "map": getattr(game, "current_map", None),
            "total": _hud_total(game),
            "world_items": len(game.world_items),
            "vida": float(game.vida),
            "escudo": float(game.escudo),
            "placed": len(game.placeables.objects),
            "arena_state": [a.state for a in game.arenas],
            "arena_done": [bool(a.completed) for a in game.arenas],
            "attached": _attached_total(game),
            "count_n": (
                None if game.no_light_timer is None
                else int(math.ceil(game.no_light_timer))
            ),
        }

    def reset(self):

        self.game = None
        self.prev = None
        self.slime_flash = {}
        self.step_t = 0.25
        self.crackle_t = 0.0
        self.heart_t = 0.0

    def update(self, game, dt, active):

        if game is None:

            self.reset()
            return

        if self.broken:
            return

        try:
            self._update(game, dt, active)

        except Exception as exc:

            self.broken = True
            print(f"[sonidos] observador desactivado: {exc!r}")

    def _update(self, game, dt, active):

        if game is not self.game:

            self.game = game
            self.prev = self._read(game)
            self.slime_flash = {}
            self.step_t = 0.25
            self.crackle_t = 0.0
            self.heart_t = 0.0
            return

        cur = self._read(game)

        if not active:

            self.prev = cur
            return

        prev = self.prev
        self.prev = cur

        play = audio.play

        if cur["slot"] != prev["slot"]:
            play("slot")

        if cur["has_match"] and not prev["has_match"]:
            play("light_on")

        if cur["magnet"] != prev["magnet"]:
            play("magnet_on" if cur["magnet"] else "magnet_off")

        if cur["msg_t"] > prev["msg_t"] + 0.3:

            text = cur["msg_text"].strip().lower()

            if text.startswith(DENY_PREFIXES):
                play("deny")
            else:
                play("msg")

        if cur["total"] < prev["total"]:

            if cur["world_items"] > prev["world_items"]:
                play("drop")

            elif cur["placed"] > prev["placed"]:
                play("place")

            elif cur["escudo"] > prev["escudo"] + 0.005:
                play("shield_up")

            elif cur["vida"] > prev["vida"] + 0.005:
                play("heal")

            else:
                play("use_item")

        elif cur["placed"] > prev["placed"]:
            play("place")

        if cur["count_n"] is not None and cur["count_n"] != prev["count_n"]:

            if 1 <= cur["count_n"] <= 10:
                play("tick_high" if cur["count_n"] <= 3 else "tick")

        if cur["state"] != prev["state"] and cur["state"] == "dying":
            play("game_over")

        for before, now in zip(prev["arena_state"], cur["arena_state"]):

            if now == "wave" and before != "wave":
                play("wave_start")

        for before, now in zip(prev["arena_done"], cur["arena_done"]):

            if now and not before:
                play("map_complete")

        if cur["attached"] > prev["attached"]:
            play("bite")

        if cur["shop"] != prev["shop"]:
            play("shop_open" if cur["shop"] else "shop_close")

        if (cur["pause"] is None) != (prev["pause"] is None):
            play("pause_open" if cur["pause"] is not None else "pause_close")

        if cur["map"] != prev["map"] and prev["map"] is not None:
            play("portal")

        self._guard("slimes", self._slimes, game, play)
        self._guard("steps", self._steps, game, dt, play)
        self._guard("crackle", self._crackle, game, dt, play)
        self._guard("objectives", self._objectives, prev, cur, play)
        self._guard("tutorial", self._tutorial, prev, cur, play)
        self._guard("heartbeat", self._heartbeat, game, dt, play)

    def _guard(self, name, fn, *args):

        if name in self.disabled:
            return

        try:
            fn(*args)

        except Exception as exc:

            self.disabled.add(name)
            print(f"[sonidos] '{name}' desactivado: {exc!r}")

    def _objectives(self, prev, cur, play):

        if cur["obj_phase"] == "done" and prev["obj_phase"] != "done":
            play("objective_done")

        elif (
            cur["obj_index"] is not None
            and prev["obj_index"] is not None
            and cur["obj_index"] > prev["obj_index"]
        ):
            play("objective_new")

    def _tutorial(self, prev, cur, play):

        if (
            cur["tut_index"] is not None
            and prev["tut_index"] is not None
            and cur["tut_index"] > prev["tut_index"]
        ):
            play("tutorial_page")

    def _heartbeat(self, game, dt, play):

        weak = (
            game.state == "playing"
            and game.pause_view is None
            and game.shop is None
            and 0.0 < float(game.vida) < HEART_LIFE
            and float(game.escudo) <= 0.0
        )

        if not weak:

            self.heart_t = HEART_INTERVAL * 0.5
            return

        self.heart_t += dt

        if self.heart_t >= HEART_INTERVAL:

            self.heart_t = 0.0
            play("heartbeat", 1.0 - float(game.vida) / HEART_LIFE * 0.5)

    def _slimes(self, game, play):

        manager = getattr(game, "slimes", None)

        flashes = {}
        hit = False

        for slime in getattr(manager, "slimes", []):

            key = id(slime)
            flash = float(getattr(slime, "flash", 0.0))

            if flash > self.slime_flash.get(key, 0.0) + 0.05:
                hit = True

            flashes[key] = flash

        self.slime_flash = flashes

        if hit:
            play("slime_hit")

    def _steps(self, game, dt, play):

        walking = (
            game.state == "playing"
            and game.pause_view is None
            and game.shop is None
            and game.tutorial is None
            and bool(getattr(game.player, "moving", False))
        )

        # si el jugador avisa cada pisada (player.pop_step), el sonido cae justo
        # cuando el pie toca el piso; si no, se usa el reloj de siempre
        pop = getattr(game.player, "pop_step", None)

        stepped = pop() if pop is not None else False

        if not walking:

            self.step_t = STEP_INTERVAL * 0.75
            return

        if pop is not None:

            if stepped:

                self.step_flip = not self.step_flip

                play("step_a" if self.step_flip else "step_b")

            return

        self.step_t += dt

        if self.step_t >= STEP_INTERVAL:

            self.step_t = 0.0
            self.step_flip = not self.step_flip

            play("step_a" if self.step_flip else "step_b")

    def _crackle(self, game, dt, play):

        self.crackle_t += dt

        if self.crackle_t < CRACKLE_INTERVAL:
            return

        self.crackle_t = 0.0

        if game.state != "playing":
            return

        px, py = game.player.rect.center
        best = 0.0

        for obj in game.placeables.objects:

            if getattr(obj, "kind", "") != "fogata":
                continue

            if not getattr(obj, "lit", False):
                continue

            cx, cy = obj.rect.center

            dist = math.hypot(cx - px, cy - py)

            if dist < CRACKLE_RANGE:
                best = max(best, (1.0 - dist / CRACKLE_RANGE) ** 1.2)

        if best > 0.02:
            play("crackle", best)


watcher = SoundWatcher()