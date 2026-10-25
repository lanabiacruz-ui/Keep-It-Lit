import math
import random
import sys
import wave
from array import array
from pathlib import Path

SR = 44100
OUT = Path(__file__).resolve().parent.parent / "assets" / "maps" / "sounds"

rng = random.Random(7)


class Sig:

    def __init__(self, values):
        self.v = list(values)

    def __len__(self):
        return len(self.v)

    def _op(self, other, fn):
        if isinstance(other, Sig):
            if len(other.v) != len(self.v):
                raise ValueError("las señales tienen distinto largo")
            return Sig(fn(a, b) for a, b in zip(self.v, other.v))
        return Sig(fn(a, other) for a in self.v)

    def __add__(self, other):
        return self._op(other, lambda a, b: a + b)

    __radd__ = __add__

    def __sub__(self, other):
        return self._op(other, lambda a, b: a - b)

    def __mul__(self, other):
        return self._op(other, lambda a, b: a * b)

    __rmul__ = __mul__

    def __pow__(self, p):
        return Sig(math.copysign(abs(a) ** p, a) for a in self.v)

    def map(self, fn):
        return Sig(fn(a) for a in self.v)

    def sign(self):
        return Sig((a > 0) - (a < 0) for a in self.v)


def zeros(n):
    return Sig([0.0] * n)


def lin(a, b, n):
    if n == 1:
        return Sig([a])
    step = (b - a) / (n - 1)
    return Sig(a + step * i for i in range(n))


def env(n, attack=0.004, decay=6.0):
    att = max(attack, 1e-4)
    out = []
    for i in range(n):
        t = i / SR
        out.append(min(1.0, t / att) * math.exp(-decay * t))
    return Sig(out)


def sine(freq, dur, phase=0.0):
    if isinstance(freq, Sig):
        out = []
        acc = 0.0
        for f in freq.v:
            acc += f
            out.append(math.sin(2 * math.pi * acc / SR + phase))
        return Sig(out)
    n = int(SR * dur)
    return Sig(
        math.sin(2 * math.pi * freq * (i / SR) + phase) for i in range(n)
    )


def sweep(f0, f1, dur, curve=1.0):
    n = int(SR * dur)
    return Sig(
        f0 + (f1 - f0) * ((i / (SR * dur)) ** curve) for i in range(n)
    )


def noise(dur):
    return Sig(rng.uniform(-1, 1) for _ in range(int(SR * dur)))


def lowpass(x, cutoff):
    a = math.exp(-2 * math.pi * cutoff / SR)
    out = []
    prev = 0.0
    for v in x.v:
        prev = (1 - a) * v + a * prev
        out.append(prev)
    return Sig(out)


def highpass(x, cutoff):
    return x - lowpass(x, cutoff)


def mix(*parts):
    n = max(len(p) for p in parts)
    out = [0.0] * n
    for p in parts:
        for i, v in enumerate(p.v):
            out[i] += v
    return Sig(out)


def delay(x, seconds, gain=1.0):
    return Sig([0.0] * int(SR * seconds) + [v * gain for v in x.v])


def save(name, x, volume=0.8):
    values = list(x.v)
    peak = max(abs(v) for v in values) or 1.0
    values = [v / peak * volume for v in values]
    fade = min(len(values), int(SR * 0.008))
    if fade > 0:
        ramp = lin(1, 0, fade).v
        for i in range(fade):
            values[len(values) - fade + i] *= ramp[i]
    data = array("h", (int(v * 32767) for v in values))
    if sys.byteorder == "big":
        data.byteswap()
    OUT.mkdir(parents=True, exist_ok=True)
    with wave.open(str(OUT / f"{name}.wav"), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(data.tobytes())
    print(f"{name}.wav  {len(values) / SR:.2f}s")


def note(freq, dur, decay=7.0, harmonics=(1.0, 0.35, 0.15)):
    out = zeros(int(SR * dur))
    for i, h in enumerate(harmonics, start=1):
        out = out + h * sine(freq * i, dur)
    return out * env(len(out), 0.003, decay)


def coin():
    a = note(1319, 0.30, 9.0)
    b = delay(note(1760, 0.45, 7.0), 0.07)
    return mix(a * 0.8, b)


def coin_big():
    a = note(988, 0.25, 8.0)
    b = delay(note(1319, 0.25, 8.0), 0.06)
    c = delay(note(1760, 0.5, 6.0), 0.12)
    return mix(a * 0.7, b * 0.8, c)


def pickup():
    return mix(
        note(523, 0.18, 12.0),
        delay(note(659, 0.18, 12.0), 0.06),
        delay(note(784, 0.3, 9.0), 0.12),
    )


def gem():
    notes = [1047, 1319, 1568, 2093]
    parts = [delay(note(f, 0.5, 6.0), 0.07 * i) for i, f in enumerate(notes)]
    return mix(*parts)


def swing():
    n = noise(0.20)
    n = highpass(lowpass(n, 5000), 600)
    e = lin(0, math.pi, len(n)).map(math.sin) ** 1.5
    return n * e


def hit():
    thump = sine(sweep(220, 60, 0.16), 0.16) * env(int(SR * 0.16), 0.002, 22)
    crack = lowpass(noise(0.08), 4000) * env(int(SR * 0.08), 0.001, 55)
    return mix(thump, crack * 0.8)


def hit_heavy():
    thump = sine(sweep(160, 40, 0.28), 0.28) * env(int(SR * 0.28), 0.002, 14)
    crack = lowpass(noise(0.14), 3000) * env(int(SR * 0.14), 0.001, 30)
    ring = sine(95, 0.3) * env(int(SR * 0.3), 0.002, 10) * 0.4
    return mix(thump, crack, ring)


def hurt():
    tone = sine(sweep(330, 110, 0.30), 0.30)
    tone = tone.sign() * 0.5 + tone * 0.5
    tone = tone * env(len(tone), 0.003, 7)
    crack = lowpass(noise(0.15), 2500) * env(int(SR * 0.15), 0.001, 25)
    return mix(tone, crack * 0.7)


def enemy_die():
    pop = sine(sweep(520, 70, 0.28, 0.6), 0.28) * env(int(SR * 0.28), 0.002, 11)
    puff = highpass(lowpass(noise(0.25), 3500), 400) * env(int(SR * 0.25), 0.002, 14)
    return mix(pop, puff * 0.8)


def fireball():
    n = highpass(lowpass(noise(0.45), 3500), 300)
    e = (lin(0, math.pi, len(n)) ** 0.9).map(math.sin) ** 1.2
    low = sine(sweep(120, 260, 0.45), 0.45) * 0.4
    return (n * 0.8 + low) * e


def shot():
    return sine(sweep(1100, 280, 0.16, 0.5), 0.16) * env(int(SR * 0.16), 0.001, 14)


def explosion():
    rumble = lowpass(noise(0.9), 400) * env(int(SR * 0.9), 0.002, 4.5)
    crack = highpass(lowpass(noise(0.25), 6000), 500) * env(int(SR * 0.25), 0.001, 16)
    boom = sine(sweep(110, 35, 0.7), 0.7) * env(int(SR * 0.7), 0.002, 5)
    return mix(rumble * 1.1, crack * 0.8, boom * 1.2)


def flashbang():
    bang = lowpass(noise(0.35), 7000) * env(int(SR * 0.35), 0.001, 12)
    boom = sine(sweep(140, 45, 0.4), 0.4) * env(int(SR * 0.4), 0.001, 8)
    ring = sine(5200, 1.6) * env(int(SR * 1.6), 0.02, 2.2) * 0.35
    ring = ring + sine(5230, 1.6) * env(int(SR * 1.6), 0.02, 2.2) * 0.25
    return mix(bang, boom * 1.1, ring)


def door_hit():
    thud = sine(sweep(180, 70, 0.14), 0.14) * env(int(SR * 0.14), 0.001, 24)
    wood = lowpass(noise(0.1), 2200) * env(int(SR * 0.1), 0.001, 40)
    return mix(thud, wood * 0.7)


def door_resist():
    out = zeros(int(SR * 0.4))
    for f, g in ((620, 1.0), (937, 0.7), (1411, 0.5), (2203, 0.3)):
        out = out + g * sine(f, 0.4)
    return out * env(len(out), 0.001, 14) * 0.8


def door_break():
    crack = highpass(lowpass(noise(0.2), 5000), 300) * env(int(SR * 0.2), 0.001, 20)
    thud = sine(sweep(150, 50, 0.4), 0.4) * env(int(SR * 0.4), 0.001, 9)
    debris = mix(*[
        delay(lowpass(noise(0.06), 3000) * env(int(SR * 0.06), 0.001, 40), d, g)
        for d, g in ((0.12, 0.5), (0.2, 0.4), (0.29, 0.3), (0.37, 0.2))
    ])
    return mix(crack, thud * 1.1, debris)


def chest_open():
    creak = sine(sweep(180, 330, 0.25), 0.25) * env(int(SR * 0.25), 0.02, 5) * 0.4
    sparkle = mix(*[
        delay(note(f, 0.4, 7.0), 0.09 * i + 0.1)
        for i, f in enumerate((784, 988, 1175, 1568))
    ])
    return mix(creak, sparkle)


def buy():
    return mix(coin() * 0.8, delay(coin_big(), 0.14))


def wave_clear():
    parts = []
    for i, f in enumerate((523, 659, 784, 1047)):
        parts.append(delay(note(f, 0.55, 4.0, (1.0, 0.5, 0.25)), 0.13 * i))
    parts.append(delay(note(1568, 0.8, 3.0, (1.0, 0.4)), 0.52))
    return mix(*parts)


def click():
    return sine(sweep(1800, 900, 0.04), 0.04) * env(int(SR * 0.04), 0.001, 70)


def light_out():
    tone = sine(sweep(440, 70, 1.1, 0.7), 1.1) * env(int(SR * 1.1), 0.01, 2.6)
    return tone + 0.3 * sine(sweep(220, 35, 1.1, 0.7), 1.1) * env(int(SR * 1.1), 0.01, 2.6)


def alert():
    return mix(note(880, 0.15, 10.0), delay(note(880, 0.15, 10.0), 0.18))


def mosquito():
    n = int(SR * 0.5)
    buzz = Sig(
        math.sin(
            2 * math.pi
            * (320 + 30 * math.sin(2 * math.pi * 28 * (i / SR)))
            * (i / SR)
        )
        for i in range(n)
    )
    buzz = buzz.sign() * 0.4 + buzz * 0.6
    return buzz * lin(0, math.pi, n).map(math.sin) * 0.6



def ui_confirm():
    return mix(
        note(660, 0.12, 22.0, (1.0, 0.2)),
        delay(note(880, 0.14, 20.0, (1.0, 0.2)), 0.05),
    )


def ui_back():
    return mix(
        note(660, 0.12, 22.0, (1.0, 0.2)),
        delay(note(440, 0.16, 18.0, (1.0, 0.2)), 0.05),
    )


def slot():
    return sine(sweep(1500, 1100, 0.05), 0.05) * env(int(SR * 0.05), 0.001, 60)


def msg():
    return note(740, 0.12, 24.0, (1.0, 0.25))


def deny():
    a = sine(160, 0.11)
    a = a.sign() * 0.4 + a * 0.6
    a = a * env(len(a), 0.003, 16)
    return mix(a, delay(a, 0.14))


def tick():
    n = int(SR * 0.04)
    return sine(sweep(1900, 1300, 0.04), 0.04) * env(n, 0.0005, 95)


def tick_high():
    n = int(SR * 0.04)
    a = sine(sweep(2600, 1800, 0.04), 0.04) * env(n, 0.0005, 95)
    return mix(a, delay(a, 0.08, 0.8))


def shop_open():
    return mix(
        note(1568, 0.45, 7.0, (1.0, 0.4, 0.2)),
        delay(note(2093, 0.5, 6.0, (1.0, 0.3)), 0.09),
    )


def shop_close():
    return mix(
        note(1319, 0.3, 9.0, (1.0, 0.4)),
        delay(note(988, 0.4, 8.0, (1.0, 0.4)), 0.09),
    )


def pause_open():
    n = int(SR * 0.22)
    return (
        sine(sweep(420, 230, 0.22), 0.22) * env(n, 0.004, 11) * 0.8
        + lowpass(noise(0.22), 1200) * env(n, 0.004, 16) * 0.2
    )


def pause_close():
    n = int(SR * 0.22)
    return (
        sine(sweep(230, 420, 0.22), 0.22) * env(n, 0.004, 11) * 0.8
        + lowpass(noise(0.22), 1200) * env(n, 0.004, 16) * 0.2
    )


def objective_new():
    return mix(
        note(784, 0.3, 8.0, (1.0, 0.3)),
        delay(note(1047, 0.4, 7.0, (1.0, 0.3)), 0.1),
    )


def objective_done():
    return mix(
        note(659, 0.35, 7.0, (1.0, 0.4, 0.2)),
        delay(note(880, 0.35, 7.0, (1.0, 0.4, 0.2)), 0.09),
        delay(note(1319, 0.6, 5.5, (1.0, 0.4)), 0.18),
    )


def tutorial_page():
    n = int(SR * 0.12)
    flick = highpass(lowpass(noise(0.12), 5000), 900)
    flick = flick * lin(0, math.pi, n).map(math.sin)
    return mix(flick * 0.7, delay(note(880, 0.1, 26.0, (1.0, 0.2)), 0.04) * 0.5)


def achievement():
    parts = [
        delay(note(f, 0.6, 5.0, (1.0, 0.5, 0.25)), 0.09 * i)
        for i, f in enumerate((659, 784, 988, 1319))
    ]
    parts.append(delay(note(2637, 0.6, 6.0, (1.0, 0.3)), 0.34) * 0.5)
    return mix(*parts)


def _step(f0, f1):
    n = int(SR * 0.10)
    thump = sine(sweep(f0, f1, 0.10), 0.10) * env(n, 0.002, 38)
    scuff = highpass(lowpass(noise(0.10), 2400), 300) * env(n, 0.001, 45)
    return mix(thump * 0.8, scuff * 0.9)


def step_a():
    return _step(150, 70)


def step_b():
    return _step(130, 60)


def light_on():
    n = int(SR * 0.55)
    puff = highpass(lowpass(noise(0.55), 3000), 400)
    swell = lin(0, math.pi, n).map(math.sin) ** 1.4
    rise = sine(sweep(180, 520, 0.55, 1.4), 0.55) * 0.25
    sparks = [
        delay(lowpass(noise(0.03), 5000) * env(int(SR * 0.03), 0.001, 90), d, 0.6)
        for d in (0.05, 0.14, 0.23, 0.31)
    ]
    return mix((puff * 0.7 + rise) * swell, *sparks)


def drop():
    n = int(SR * 0.14)
    thud = sine(sweep(320, 110, 0.14), 0.14) * env(n, 0.002, 26)
    rustle = lowpass(noise(0.08), 1800) * env(int(SR * 0.08), 0.001, 50)
    return mix(thud, rustle * 0.5)


def use_item():
    n = int(SR * 0.12)
    a = sine(sweep(260, 620, 0.12), 0.12) * env(n, 0.004, 14)
    b = sine(sweep(300, 700, 0.12), 0.12) * env(n, 0.004, 14)
    return mix(a, delay(b, 0.11, 0.9))


def heal():
    return mix(*[
        delay(note(f, 0.45, 5.0, (1.0, 0.3)), 0.09 * i)
        for i, f in enumerate((523, 659, 784, 1047))
    ])


def shield_up():
    n = int(SR * 0.7)
    s1 = sine(sweep(380, 980, 0.7, 0.8), 0.7)
    s2 = sine(sweep(390, 1000, 0.7, 0.8), 0.7)
    shimmer = (s1 * 0.5 + s2 * 0.5) * env(n, 0.05, 3.2)
    ping = delay(note(1568, 0.5, 6.0, (1.0, 0.4)), 0.35)
    return mix(shimmer * 0.8, ping * 0.7)


def _magnet(f0, f1):
    n = int(SR * 0.32)
    buzz = sine(sweep(f0, f1, 0.32, 1.5), 0.32)
    buzz = buzz.sign() * 0.35 + buzz * 0.65
    hiss = highpass(lowpass(noise(0.32), 2500), 500) * env(n, 0.01, 9)
    return buzz * env(n, 0.01, 5.0) * 0.8 + hiss * 0.25


def magnet_on():
    return _magnet(120, 340)


def magnet_off():
    return _magnet(340, 120)


def game_over():
    parts = [
        delay(note(f, 0.9, 3.2, (1.0, 0.5, 0.2)), 0.28 * i)
        for i, f in enumerate((392, 330, 262, 196))
    ]
    drone = sine(sweep(110, 55, 1.6), 1.6) * env(int(SR * 1.6), 0.05, 1.8) * 0.5
    return mix(*parts, drone)


def wave_start():
    def drum(when):
        body = sine(sweep(130, 48, 0.3), 0.3) * env(int(SR * 0.3), 0.002, 9)
        skin = lowpass(noise(0.1), 1500) * env(int(SR * 0.1), 0.001, 40)
        return delay(mix(body, skin * 0.5), when)

    n = int(SR * 0.7)
    horn = zeros(n)
    for i, h in enumerate((1.0, 0.6, 0.4, 0.25), start=1):
        horn = horn + h * sine(196 * i, 0.7)
    horn = horn * env(n, 0.12, 2.6) * 0.5
    return mix(drum(0.0), drum(0.22), delay(horn, 0.15))


def map_complete():
    chords = (
        (523, 659, 784),
        (587, 740, 880),
        (659, 784, 988),
        (784, 988, 1175, 1568),
    )
    parts = []
    for i, chord in enumerate(chords):
        for f in chord:
            dur = 0.9 if i == len(chords) - 1 else 0.5
            parts.append(delay(note(f, dur, 4.5, (1.0, 0.4, 0.15)), 0.22 * i) * 0.5)
    parts.append(note(392, 1.4, 3.0, (1.0, 0.5)) * 0.6)
    return mix(*parts)


def portal():
    n = int(SR * 0.7)
    sway = lin(0, math.pi, n).map(math.sin)
    freq = Sig(
        300 + (i / n) * 900 + 40 * math.sin(2 * math.pi * 9 * i / SR)
        for i in range(n)
    )
    air = highpass(lowpass(noise(0.7), 4000), 500)
    return sine(freq, 0.7) * sway * 0.7 + air * sway * 0.3


def place():
    n = int(SR * 0.14)
    thunk = sine(sweep(220, 90, 0.14), 0.14) * env(n, 0.002, 24)
    knock = lowpass(noise(0.05), 2800) * env(int(SR * 0.05), 0.001, 60)
    return mix(thunk, knock * 0.6)


def bite():
    chomps = [
        delay(lowpass(noise(0.07), 3200) * env(int(SR * 0.07), 0.001, 38), d, g)
        for d, g in ((0.0, 1.0), (0.08, 0.8), (0.17, 0.6))
    ]
    growl = sine(sweep(140, 90, 0.3), 0.3) * env(int(SR * 0.3), 0.01, 8) * 0.5
    return mix(*chomps, growl)


def slime_hit():
    n = int(SR * 0.18)
    freq = Sig(
        520 - 380 * (i / n) + 60 * math.sin(2 * math.pi * 34 * i / SR)
        for i in range(n)
    )
    squelch = lowpass(noise(0.18), 1600) * env(n, 0.002, 22)
    return sine(freq, 0.18) * env(n, 0.003, 14) * 0.8 + squelch * 0.35


def crackle():
    bed = lowpass(noise(0.9), 700) * 0.12
    parts = [bed]
    for _ in range(14):
        when = rng.uniform(0.0, 0.8)
        gain = rng.uniform(0.3, 1.0)
        dur = rng.uniform(0.01, 0.03)
        pop = highpass(lowpass(noise(dur), 6000), 800)
        parts.append(delay(pop * env(len(pop), 0.0005, 150), when, gain))
    return mix(*parts)


def heartbeat():
    def thump(gain):
        n = int(SR * 0.16)
        return sine(sweep(75, 42, 0.16), 0.16) * env(n, 0.004, 17) * gain

    return mix(thump(1.0), delay(thump(0.7), 0.2))


def _talk(base, wobble=0.06, rise=0.12):
    # blip corto y agudo con un temblor rapido: "bu-ru-bu-ru" cuando habla el fantasma
    dur = 0.075
    n = int(SR * dur)
    f = Sig(
        base * (1 + rise * i / n)
        * (1 + wobble * math.sin(2 * math.pi * 36 * i / SR))
        for i in range(n)
    )
    tone = sine(f, dur) + 0.30 * sine(f * 2, dur) + 0.10 * sine(f * 3, dur)
    return tone * env(n, 0.002, 26)


def talk_a():
    return _talk(1080)


def talk_b():
    return _talk(1240, 0.05, 0.08)


def talk_c():
    return _talk(1410, 0.07, 0.15)


def talk_d():
    return _talk(1590, 0.05, 0.10)


SOUNDS = {
    "coin": coin, "coin_big": coin_big, "pickup": pickup, "gem": gem,
    "swing": swing, "hit": hit, "hit_heavy": hit_heavy, "hurt": hurt,
    "enemy_die": enemy_die, "fireball": fireball, "shot": shot,
    "explosion": explosion, "flashbang": flashbang,
    "door_hit": door_hit, "door_resist": door_resist,
    "door_break": door_break, "chest_open": chest_open, "buy": buy,
    "wave_clear": wave_clear, "click": click, "light_out": light_out,
    "alert": alert, "mosquito": mosquito,
    "ui_confirm": ui_confirm, "ui_back": ui_back, "slot": slot,
    "msg": msg, "deny": deny, "tick": tick, "tick_high": tick_high,
    "shop_open": shop_open, "shop_close": shop_close,
    "pause_open": pause_open, "pause_close": pause_close,
    "objective_new": objective_new, "objective_done": objective_done,
    "tutorial_page": tutorial_page, "achievement": achievement,
    "step_a": step_a, "step_b": step_b, "light_on": light_on,
    "drop": drop, "use_item": use_item, "heal": heal,
    "shield_up": shield_up, "magnet_on": magnet_on,
    "magnet_off": magnet_off, "game_over": game_over,
    "wave_start": wave_start, "map_complete": map_complete,
    "portal": portal, "place": place, "bite": bite,
    "slime_hit": slime_hit, "crackle": crackle, "heartbeat": heartbeat,
    "talk_a": talk_a, "talk_b": talk_b, "talk_c": talk_c, "talk_d": talk_d,
}


if __name__ == "__main__":

    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    force = "--force" in sys.argv[1:]

    for name, fn in SOUNDS.items():

        if args and name not in args:
            continue

        if not args and not force and (OUT / f"{name}.wav").exists():
            continue

        save(name, fn())