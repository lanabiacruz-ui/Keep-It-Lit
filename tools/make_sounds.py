"""Genera los efectos de sonido de Keep It Lit en assets/sounds/*.wav.

Los sonidos ya vienen generados: este script solo hace falta si queres
cambiarlos (necesita numpy: pip install numpy). Se corre desde la
carpeta del proyecto:

    python tools/make_sounds.py
"""

import wave
from pathlib import Path

import numpy as np

SR = 44100
OUT = Path(__file__).resolve().parent.parent / "assets" / "sounds"

rng = np.random.default_rng(7)


def t_axis(dur):
    return np.arange(int(SR * dur)) / SR


def env(n, attack=0.004, decay=6.0):
    """Entra rapido y se apaga exponencialmente."""
    t = np.arange(n) / SR
    a = np.minimum(1.0, t / max(attack, 1e-4))
    return a * np.exp(-decay * t)


def sine(freq, dur, phase=0.0):
    t = t_axis(dur)
    if np.isscalar(freq):
        return np.sin(2 * np.pi * freq * t + phase)
    # freq puede ser una curva (barrido)
    return np.sin(2 * np.pi * np.cumsum(freq) / SR + phase)


def sweep(f0, f1, dur, curve=1.0):
    k = (np.arange(int(SR * dur)) / (SR * dur)) ** curve
    return f0 + (f1 - f0) * k


def noise(dur):
    return rng.uniform(-1, 1, int(SR * dur))


def lowpass(x, cutoff):
    """Filtro de un polo (suaviza el ruido)."""
    a = np.exp(-2 * np.pi * cutoff / SR)
    y = np.empty_like(x)
    prev = 0.0
    for i, v in enumerate(x):
        prev = (1 - a) * v + a * prev
        y[i] = prev
    return y


def highpass(x, cutoff):
    return x - lowpass(x, cutoff)


def mix(*parts):
    n = max(len(p) for p in parts)
    out = np.zeros(n)
    for p in parts:
        out[:len(p)] += p
    return out


def delay(x, seconds, gain=1.0):
    pad = np.zeros(int(SR * seconds))
    return np.concatenate([pad, x * gain])


def save(name, x, volume=0.8):
    x = np.asarray(x, dtype=float)
    peak = np.max(np.abs(x)) or 1.0
    x = x / peak * volume
    # fundido final cortito para que no haga "clic"
    fade = min(len(x), int(SR * 0.008))
    x[-fade:] *= np.linspace(1, 0, fade)
    data = (x * 32767).astype("<i2")
    OUT.mkdir(parents=True, exist_ok=True)
    with wave.open(str(OUT / f"{name}.wav"), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(data.tobytes())
    print(f"{name}.wav  {len(x) / SR:.2f}s")


def note(freq, dur, decay=7.0, harmonics=(1.0, 0.35, 0.15)):
    out = np.zeros(int(SR * dur))
    for i, h in enumerate(harmonics, start=1):
        out += h * sine(freq * i, dur)
    return out * env(len(out), 0.003, decay)


# ---------------- sonidos ----------------

def coin():
    # dos notas agudas brillantes (tipo moneda)
    a = note(1319, 0.30, 9.0)            # E6
    b = delay(note(1760, 0.45, 7.0), 0.07)  # A6
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
    e = np.sin(np.linspace(0, np.pi, len(n))) ** 1.5
    return n * e


def hit():
    # golpe seco: "thump" grave + chasquido
    thump = sine(sweep(220, 60, 0.16), 0.16) * env(int(SR * 0.16), 0.002, 22)
    crack = lowpass(noise(0.08), 4000) * env(int(SR * 0.08), 0.001, 55)
    return mix(thump, crack * 0.8)


def hit_heavy():
    thump = sine(sweep(160, 40, 0.28), 0.28) * env(int(SR * 0.28), 0.002, 14)
    crack = lowpass(noise(0.14), 3000) * env(int(SR * 0.14), 0.001, 30)
    ring = sine(95, 0.3) * env(int(SR * 0.3), 0.002, 10) * 0.4
    return mix(thump, crack, ring)


def hurt():
    # el jugador recibe dano: tono grave que cae + ruido
    tone = sine(sweep(330, 110, 0.30), 0.30)
    tone = np.sign(tone) * 0.5 + tone * 0.5   # un poco "sucio"
    tone *= env(len(tone), 0.003, 7)
    crack = lowpass(noise(0.15), 2500) * env(int(SR * 0.15), 0.001, 25)
    return mix(tone, crack * 0.7)


def enemy_die():
    pop = sine(sweep(520, 70, 0.28, 0.6), 0.28) * env(int(SR * 0.28), 0.002, 11)
    puff = highpass(lowpass(noise(0.25), 3500), 400) * env(int(SR * 0.25), 0.002, 14)
    return mix(pop, puff * 0.8)


def fireball():
    n = highpass(lowpass(noise(0.45), 3500), 300)
    e = np.sin(np.linspace(0, np.pi, len(n)) ** 0.9) ** 1.2
    low = sine(sweep(120, 260, 0.45), 0.45) * 0.4
    return (n * 0.8 + low) * e


def shot():
    pew = sine(sweep(1100, 280, 0.16, 0.5), 0.16) * env(int(SR * 0.16), 0.001, 14)
    return pew


def explosion():
    rumble = lowpass(noise(0.9), 400) * env(int(SR * 0.9), 0.002, 4.5)
    crack = highpass(lowpass(noise(0.25), 6000), 500) * env(int(SR * 0.25), 0.001, 16)
    boom = sine(sweep(110, 35, 0.7), 0.7) * env(int(SR * 0.7), 0.002, 5)
    return mix(rumble * 1.1, crack * 0.8, boom * 1.2)


def flashbang():
    bang = lowpass(noise(0.35), 7000) * env(int(SR * 0.35), 0.001, 12)
    boom = sine(sweep(140, 45, 0.4), 0.4) * env(int(SR * 0.4), 0.001, 8)
    ring = sine(5200, 1.6) * env(int(SR * 1.6), 0.02, 2.2) * 0.35
    ring += sine(5230, 1.6) * env(int(SR * 1.6), 0.02, 2.2) * 0.25
    return mix(bang, boom * 1.1, ring)


def door_hit():
    thud = sine(sweep(180, 70, 0.14), 0.14) * env(int(SR * 0.14), 0.001, 24)
    wood = lowpass(noise(0.1), 2200) * env(int(SR * 0.1), 0.001, 40)
    return mix(thud, wood * 0.7)


def door_resist():
    # "clank" metalico
    out = np.zeros(int(SR * 0.4))
    for f, g in ((620, 1.0), (937, 0.7), (1411, 0.5), (2203, 0.3)):
        out += g * sine(f, 0.4)
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
    # se apaga la luz / game over: tono que baja lento
    tone = sine(sweep(440, 70, 1.1, 0.7), 1.1) * env(int(SR * 1.1), 0.01, 2.6)
    return tone + 0.3 * sine(sweep(220, 35, 1.1, 0.7), 1.1) * env(int(SR * 1.1), 0.01, 2.6)


def alert():
    return mix(note(880, 0.15, 10.0), delay(note(880, 0.15, 10.0), 0.18))


def mosquito():
    t = t_axis(0.5)
    buzz = np.sin(2 * np.pi * (320 + 30 * np.sin(2 * np.pi * 28 * t)) * t)
    buzz = np.sign(buzz) * 0.4 + buzz * 0.6
    return buzz * np.sin(np.linspace(0, np.pi, len(t))) * 0.6


SOUNDS = {
    "coin": coin, "coin_big": coin_big, "pickup": pickup, "gem": gem,
    "swing": swing, "hit": hit, "hit_heavy": hit_heavy, "hurt": hurt,
    "enemy_die": enemy_die, "fireball": fireball, "shot": shot,
    "explosion": explosion, "flashbang": flashbang,
    "door_hit": door_hit, "door_resist": door_resist,
    "door_break": door_break, "chest_open": chest_open, "buy": buy,
    "wave_clear": wave_clear, "click": click, "light_out": light_out,
    "alert": alert, "mosquito": mosquito,
}

if __name__ == "__main__":
    for name, fn in SOUNDS.items():
        save(name, fn())