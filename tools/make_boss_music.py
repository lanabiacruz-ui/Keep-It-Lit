"""Genera la musica y los sonidos del jefe (Pina Colosal).

Crea en assets/maps/sounds:
    boss_intro.wav    entrada epica (sube la tension y revienta en el golpe)
    boss_slam.wav     golpe/acorde suelto (entradas repetidas)
    boss_roar.wav     rugido grave
    boss_victory.wav  fanfarria de victoria
    jefe.wav          musica de la pelea (loop, 16 compases en Re menor)

Se ejecuta con:  python tools/make_boss_music.py
Necesita numpy y scipy.
"""

import wave
from pathlib import Path

import numpy as np
from scipy import signal

SR = 44100
OUT = Path(__file__).resolve().parent.parent / "assets" / "maps" / "sounds"

# segundo (dentro de boss_intro.wav) en el que revienta el golpe.
# Tiene que coincidir con BOSS_INTRO_SLAM en world/boss_cinematic.py
SLAM_T = 4.6

rng = np.random.default_rng(11)


# --------------------------------------------------------------- utilidades

def mtof(m):
    return 440.0 * 2.0 ** ((m - 69) / 12.0)


def tvec(dur):
    return np.arange(int(dur * SR)) / SR


def lowpass(x, cutoff, order=2):
    b, a = signal.butter(order, min(cutoff, SR * 0.45) / (SR / 2), "low")
    return signal.lfilter(b, a, x)


def highpass(x, cutoff, order=2):
    b, a = signal.butter(order, cutoff / (SR / 2), "high")
    return signal.lfilter(b, a, x)


def bandpass(x, lo, hi, order=2):
    b, a = signal.butter(order, [lo / (SR / 2), min(hi, SR * 0.45) / (SR / 2)], "band")
    return signal.lfilter(b, a, x)


def saw_phase(phase):
    return 2.0 * (phase - np.floor(phase + 0.5))


def saw(freq, dur, detune=0.0):
    t = tvec(dur)
    f = freq * (1.0 + detune)
    return saw_phase(f * t)


def square(freq, dur, duty=0.5):
    t = tvec(dur)
    return np.where(((freq * t) % 1.0) < duty, 1.0, -1.0)


def sine(freq, dur):
    return np.sin(2 * np.pi * freq * tvec(dur))


def adsr(n, a, d, s, r):
    """Envolvente de n muestras (tiempos en segundos)."""
    a_n = max(1, int(a * SR))
    d_n = max(1, int(d * SR))
    r_n = max(1, int(r * SR))
    env = np.ones(n) * s
    a_n = min(a_n, n)
    env[:a_n] = np.linspace(0, 1, a_n)
    d_end = min(n, a_n + d_n)
    env[a_n:d_end] = np.linspace(1, s, d_end - a_n)
    r_n = min(r_n, n)
    env[n - r_n:] *= np.linspace(1, 0, r_n)
    return env


def expdecay(n, tau):
    return np.exp(-np.arange(n) / SR / tau)


def noise(dur):
    return rng.uniform(-1, 1, int(dur * SR))


def place(buf, sig, start, gain=1.0):
    i = int(start * SR)

    if i >= len(buf):
        return

    n = min(len(sig), len(buf) - i)

    buf[i:i + n] += sig[:n] * gain


def reverb(x, seconds=2.2, wet=0.3, damp=3500):
    n = int(seconds * SR)
    t = np.arange(n) / SR
    ir = rng.uniform(-1, 1, n) * np.exp(-t * (6.0 / seconds))
    ir = lowpass(ir, damp, 1)
    ir[0] = 0.0
    tail = np.zeros(len(x) + n)
    conv = signal.fftconvolve(x, ir)
    tail[:len(conv)] = conv[:len(tail)]
    tail /= max(1e-6, np.max(np.abs(tail))) / max(1e-6, np.max(np.abs(x)))
    out = np.zeros(len(x) + n)
    out[:len(x)] += x * (1.0 - wet * 0.5)
    out += tail * wet
    return out


def soft_clip(x, drive=1.0):
    return np.tanh(x * drive)


def save(name, x, peak=0.89):
    x = np.nan_to_num(x)
    m = np.max(np.abs(x))

    if m > 0:
        x = x / m * peak

    # fade cortito para que no haga "click" al empezar/terminar
    f = int(0.004 * SR)
    x[:f] *= np.linspace(0, 1, f)
    x[-f:] *= np.linspace(1, 0, f)

    OUT.mkdir(parents=True, exist_ok=True)

    path = OUT / f"{name}.wav"

    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((x * 32767).astype("<i2").tobytes())

    print(f"{path.name}: {len(x) / SR:.1f}s")


# ------------------------------------------------------------------ voces

def timpani(freq=80.0, dur=0.9, power=1.0):
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = freq * (1.0 + 0.9 * np.exp(-t * 18.0))
    ph = 2 * np.pi * np.cumsum(f) / SR
    body = np.sin(ph) * expdecay(n, 0.22)
    skin = lowpass(noise(dur), 700) * expdecay(n, 0.03) * 0.8
    return (body + skin) * power


def kick(dur=0.45):
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = 42 + 110 * np.exp(-t * 28.0)
    ph = 2 * np.pi * np.cumsum(f) / SR
    return np.sin(ph) * expdecay(n, 0.13) + lowpass(noise(dur), 1500) * expdecay(n, 0.01) * 0.5


def snare(dur=0.35):
    n = int(dur * SR)
    body = np.sin(2 * np.pi * 190 * tvec(dur)) * expdecay(n, 0.05) * 0.5
    nz = highpass(noise(dur), 1200) * expdecay(n, 0.09)
    return body + nz * 0.9


def hat(dur=0.08):
    n = int(dur * SR)
    return highpass(noise(dur), 6500) * expdecay(n, 0.018)


def crash(dur=3.0):
    n = int(dur * SR)
    return highpass(noise(dur), 3000) * expdecay(n, 0.9)


def pad_note(m, dur, bright=1800, vol=1.0, a=0.35, r=0.5):
    f = mtof(m)
    x = saw(f, dur, -0.004) + saw(f, dur, 0.0) + saw(f, dur, 0.004)
    x = lowpass(x, bright) * adsr(len(x), a, 0.2, 0.8, r)
    return x * vol / 3.0


def brass_note(m, dur, bright=2600, vol=1.0, a=0.03, r=0.25):
    f = mtof(m)
    x = saw(f, dur, -0.003) + saw(f, dur, 0.003) + 0.5 * square(f, dur, 0.4)
    x = lowpass(x, bright) * adsr(len(x), a, 0.15, 0.75, r)
    return x * vol / 2.5


def bass_note(m, dur, vol=1.0):
    f = mtof(m)
    x = saw(f, dur) * 0.7 + sine(f, dur) * 0.9
    x = lowpass(x, 420) * adsr(len(x), 0.005, 0.08, 0.7, 0.06)
    return x * vol


def lead_note(m, dur, vol=1.0):
    f = mtof(m)
    t = tvec(dur)
    vib = 1.0 + 0.006 * np.sin(2 * np.pi * 5.5 * t) * np.minimum(1.0, t / 0.25)
    ph = 2 * np.pi * np.cumsum(f * vib) / SR
    x = (saw_phase(ph / (2 * np.pi)) + 0.6 * np.sin(ph) + 0.3 * saw_phase(ph / (2 * np.pi) * 2.0)) * 0.6
    x = lowpass(x, 3400) * adsr(len(x), 0.02, 0.12, 0.8, 0.12)
    return x * vol


def triad(root, minor=True):
    return [root, root + (3 if minor else 4), root + 7]


# --------------------------------------------------------------- boom (golpe)

def make_slam(dur=4.5):
    n = int(dur * SR)
    out = np.zeros(n)

    t = np.arange(n) / SR

    # boom grave: seno con caida de tono
    f = 28 + 90 * np.exp(-t * 4.0)
    ph = 2 * np.pi * np.cumsum(f) / SR
    boom = np.sin(ph) * np.exp(-t / 1.4)

    # golpe seco inicial
    thump = lowpass(noise(dur), 500) * np.exp(-t / 0.12)

    # rompe como un trueno
    crack = bandpass(noise(dur), 200, 5000) * np.exp(-t / 0.5)

    out += soft_clip(boom * 1.3, 1.4) * 0.9
    out += thump * 0.8
    out += crack * 0.35

    # acorde de bronces en Re menor, abierto y grave
    for m in (38, 45, 50, 53, 57, 62):
        out += place_new(n, brass_note(m, 3.6, bright=2200, vol=0.5, a=0.02, r=1.6), 0.03)

    out += place_new(n, crash(3.8), 0.0) * 0.22

    return out


def place_new(n, sig, start):
    buf = np.zeros(n)
    place(buf, sig, start)
    return buf


# ------------------------------------------------------------ boss_intro.wav

def make_intro():
    total = SLAM_T + 5.2
    n = int(total * SR)
    out = np.zeros(n)

    pre_n = int(SLAM_T * SR)
    pre_t = np.arange(pre_n) / SR
    k = pre_t / SLAM_T

    # drone grave que se abre
    drone = (saw(36.7, SLAM_T) + saw(36.7, SLAM_T, 0.006) + saw(73.4, SLAM_T, -0.004) * 0.7)
    cutoff = 90 + 900 * k ** 2

    blocks = 40
    step = pre_n // blocks
    z = None
    filt = np.zeros(pre_n)

    for i in range(blocks):

        a, b = i * step, pre_n if i == blocks - 1 else (i + 1) * step

        bb, aa = signal.butter(2, min(cutoff[a], 8000) / (SR / 2), "low")

        if z is None:
            z = signal.lfilter_zi(bb, aa) * 0.0

        filt[a:b], z = signal.lfilter(bb, aa, drone[a:b], zi=z)

    out[:pre_n] += filt * (0.08 + 0.55 * k ** 1.5) * 0.7

    # subida de tono (como un grito que sube)
    f = 80 * (4.8 ** (k ** 1.3))
    ph = 2 * np.pi * np.cumsum(f * (1 + 0.004 * np.sin(2 * np.pi * 6 * pre_t))) / SR
    sweep = (saw_phase(ph / (2 * np.pi)) * 0.6 + np.sin(ph) * 0.5)
    sweep = lowpass(sweep, 2400)
    out[:pre_n] += sweep * (k ** 2.2) * 0.35

    # ruido que sube de frecuencia (viento / tension)
    nz = noise(SLAM_T)
    res = np.zeros(pre_n)
    z = None

    for i in range(blocks):

        a, b = i * step, pre_n if i == blocks - 1 else (i + 1) * step

        c = 300 + 6500 * (a / pre_n) ** 1.6

        bb, aa = signal.butter(2, [c / (SR / 2) * 0.7, min(c * 1.5, 18000) / (SR / 2)], "band")

        if z is None:
            z = signal.lfilter_zi(bb, aa) * 0.0

        res[a:b], z = signal.lfilter(bb, aa, nz[a:b], zi=z)

    out[:pre_n] += res * (k ** 2.0) * 0.55

    # latidos de timbal que se aceleran
    t_hit = 0.35
    interval = 1.05

    while t_hit < SLAM_T - 0.25:

        kk = t_hit / SLAM_T

        place(out, timpani(70 + 25 * kk, 0.9), t_hit, 0.45 + 0.55 * kk)

        # doble golpe (latido) cada vez mas pegado
        place(out, timpani(66 + 25 * kk, 0.7), t_hit + 0.17 + 0.0, 0.3 + 0.4 * kk)

        interval = max(0.38, interval * 0.88)
        t_hit += interval

    # el golpe
    slam = make_slam(5.2)
    place(out, slam, SLAM_T, 1.15)

    out = reverb(out, 2.6, 0.22)[:n]

    return soft_clip(out, 1.1)


# ------------------------------------------------------------------ rugido

def make_roar(dur=2.6):
    n = int(dur * SR)
    t = np.arange(n) / SR

    f0 = 62 * np.exp(-t * 0.28) * (1 + 0.04 * np.sin(2 * np.pi * 7 * t))
    ph = 2 * np.pi * np.cumsum(f0) / SR
    growl = saw_phase(ph / (2 * np.pi)) * (0.55 + 0.45 * np.sin(2 * np.pi * 31 * t))
    growl += 0.6 * saw_phase(ph / (2 * np.pi) * 1.5)

    # formantes que "abren la boca"
    air = noise(dur)
    mouth = np.zeros(n)
    blocks = 30
    step = n // blocks
    z = None

    for i in range(blocks):

        a, b = i * step, n if i == blocks - 1 else (i + 1) * step

        kk = np.sin(np.pi * min(1, i / blocks * 1.2))

        c = 350 + 700 * kk

        bb, aa = signal.butter(2, [c * 0.8 / (SR / 2), c * 1.25 / (SR / 2)], "band")

        if z is None:
            z = signal.lfilter_zi(bb, aa) * 0.0

        mouth[a:b], z = signal.lfilter(bb, aa, air[a:b], zi=z)

    x = growl * 0.8 + mouth * 2.2

    x = soft_clip(x * 1.6, 1.3)
    x = lowpass(x, 3200)

    env = adsr(n, 0.12, 0.5, 0.75, 1.1)

    return x * env


# ------------------------------------------------------------- victoria

def make_victory():
    total = 9.0
    n = int(total * SR)
    out = np.zeros(n)

    # redoble de timbales que sube
    t_hit = 0.0
    gap = 0.16

    while t_hit < 1.4:
        place(out, timpani(88, 0.5), t_hit, 0.25 + 0.5 * (t_hit / 1.4))
        t_hit += gap
        gap = max(0.07, gap * 0.9)

    place(out, timpani(60, 1.6, 1.2), 1.4, 1.0)
    place(out, crash(3.5), 1.4, 0.2)

    # fanfarria en Re mayor
    mel = [
        (1.4, 0.45, 69), (1.85, 0.45, 74), (2.3, 1.5, 78),
        (3.9, 0.45, 76), (4.35, 0.45, 74), (4.8, 0.45, 73),
        (5.25, 2.6, 74),
    ]

    for start, dur, m in mel:
        place(out, brass_note(m + 0, dur + 0.15, 3200, 1.0, 0.025, 0.25), start, 0.55)
        place(out, brass_note(m - 12, dur + 0.15, 2400, 1.0, 0.03, 0.25), start, 0.4)

    chords = [
        (1.4, 1.6, (50, 57, 62, 66)),
        (3.0, 0.9, (43, 50, 59, 62)),
        (3.9, 1.35, (45, 52, 57, 61)),
        (5.25, 3.4, (38, 45, 50, 54, 57)),
    ]

    for start, dur, notes in chords:
        for m in notes:
            place(out, pad_note(m, dur + 0.4, 2600, 1.0, 0.05, 0.9), start, 0.34)

    place(out, bass_note(38, 3.4, 1.0), 5.25, 0.8)
    place(out, bass_note(38, 1.5, 1.0), 1.4, 0.8)

    # brillos finales
    for i, m in enumerate((86, 90, 93, 98, 102)):
        place(out, sine(mtof(m), 1.6) * expdecay(int(1.6 * SR), 0.5), 6.2 + i * 0.16, 0.07)

    out = reverb(out, 3.0, 0.3)[:n]

    fade = int(2.2 * SR)
    out[-fade:] *= np.linspace(1.0, 0.0, fade) ** 1.5

    return soft_clip(out, 1.05)


# ---------------------------------------------------------- musica del jefe

BPM = 144
BEAT = 60.0 / BPM
BAR = BEAT * 4
BARS = 16

# (raiz del bajo, es menor)
PROG = [
    (38, True), (34, False), (43, True), (45, False),   # Dm  Bb  Gm  A
    (38, True), (34, False), (36, False), (45, False),  # Dm  Bb  C   A
]

MELODY = [
    [(0, 1.5, 74), (1.5, 0.5, 72), (2, 2, 69)],
    [(0, 1.5, 70), (1.5, 0.5, 72), (2, 2, 74)],
    [(0, 1.5, 74), (1.5, 0.5, 75), (2, 1, 77), (3, 1, 74)],
    [(0, 2, 73), (2, 1, 74), (3, 1, 76)],
    [(0, 1.5, 77), (1.5, 0.5, 76), (2, 2, 74)],
    [(0, 1.5, 74), (1.5, 0.5, 72), (2, 2, 70)],
    [(0, 1, 72), (1, 1, 74), (2, 1, 76), (3, 1, 79)],
    [(0, 2, 76), (2, 2, 73)],
]


def make_loop():
    dur = BAR * BARS
    tail = 3.0
    n = int((dur + tail) * SR)
    out = np.zeros(n)

    kick_s = kick()
    snare_s = snare()
    hat_s = hat()

    for bar in range(BARS):

        t0 = bar * BAR

        root, minor = PROG[bar % 8]

        second = bar >= 8

        # ---- percusion: golpes de taiko con galope
        for beat in range(4):
            place(out, kick_s, t0 + beat * BEAT, 0.95 if beat % 2 == 0 else 0.7)

        for step_i in (1.5, 3.5):
            place(out, timpani(70, 0.5), t0 + step_i * BEAT, 0.45)

        for beat in (1, 3):
            place(out, snare_s, t0 + beat * BEAT, 0.7)

        for e in range(8):
            place(out, hat_s, t0 + e * BEAT * 0.5, 0.28 if e % 2 else 0.18)

        if bar % 8 == 0:
            place(out, crash(), t0, 0.28)

        if bar % 4 == 3:
            # relleno de toms al final de cada frase
            for q in range(4):
                place(out, timpani(95 - q * 8, 0.35), t0 + (3 + q * 0.25) * BEAT, 0.5)

        # ---- bajo en corcheas (con acento en el tiempo 1)
        for e in range(8):
            m = root if e % 4 != 3 else root + 12
            place(out, bass_note(m, BEAT * 0.55), t0 + e * BEAT * 0.5, 0.95 if e == 0 else 0.62)

        # ---- cuerdas (acorde sostenido)
        notes = [root + 12 + x for x in triad(root, minor)] + [root + 24]

        for m in notes:
            place(out, pad_note(m, BAR + 0.3, 1700, 1.0, 0.35, 0.5), t0, 0.22 if not second else 0.3)

        # ---- arpegio rapido (da empuje)
        arp = triad(root, minor) + [12 + root]

        for s in range(16):
            m = root + 24 + (arp[s % 4] - root)
            place(out, lead_note(m, BEAT * 0.22, 0.5) * 0.5, t0 + s * BEAT * 0.25, 0.14 if not second else 0.2)

        # ---- bronces: golpes cortos en el 1 y el "y" del 3
        if second:
            for hit in (0, 2.5):
                for m in notes[:3]:
                    place(out, brass_note(m + 12, BEAT * 1.3, 2400, 1.0, 0.02, 0.2), t0 + hit * BEAT, 0.2)

        # ---- melodia heroica (segunda mitad)
        if second:
            for start, d, m in MELODY[bar - 8]:
                place(out, lead_note(m, d * BEAT, 1.0), t0 + start * BEAT, 0.42)
                place(out, lead_note(m - 12, d * BEAT, 1.0), t0 + start * BEAT, 0.16)

    out = reverb(out, 1.8, 0.2)

    # el final de la reverb se pliega al principio -> el loop no corta
    loop_n = int(dur * SR)
    body = out[:loop_n].copy()
    wrap = out[loop_n:loop_n + (len(out) - loop_n)]
    body[:len(wrap)] += wrap[:len(body)]

    return soft_clip(body * 0.95, 1.1)


def main():

    save("boss_intro", make_intro())
    save("boss_slam", make_slam(4.5))
    save("boss_roar", make_roar())
    save("boss_victory", make_victory())
    save("jefe", make_loop(), peak=0.8)


if __name__ == "__main__":
    main()