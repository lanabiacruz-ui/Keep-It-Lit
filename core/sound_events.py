import math

from core.audio_manager import audio

STEP_INTERVAL = 0.34
CRACKLE_INTERVAL = 1.15
CRACKLE_RANGE = 420.0


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

    def _read(self, game):

        return {
            "slot": game.selected_slot,
            "has_match": bool(game.has_match),
            "magnet": bool(game.magnet_mode),
            "msg_t": float(getattr(game, "message_timer", 0.0) or 0.0),
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

        self._slimes(game, play)
        self._steps(game, dt, play)
        self._crackle(game, dt, play)

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

        if not walking:

            self.step_t = STEP_INTERVAL * 0.75
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
