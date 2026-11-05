"""Genera la musica de la tienda: assets/maps/sounds/tienda.ogg

Piano electrico suave, bajo redondo, un colchon de acordes y una
campanita (kalimba) que apenas se escucha. Sin bateria, tempo lento,
16 compases en Do mayor (72 bpm, ~53 s) y cierra en loop sin cortes: todo
se suma "dando la vuelta" y la reverb es circular, asi que la cola del
final se mezcla con el principio.

Se ejecuta con:  python tools/make_shop_music.py
Necesita numpy. Si hay ffmpeg lo pasa a .ogg (si no, deja el .wav, que el
gestor de musica tambien levanta).
"""

import shutil
import subprocess
import wave
from pathlib import Path

import numpy as np

SR = 44100
BPM = 72
BEAT = 60.0 / BPM
BAR = BEAT * 4
BARS = 16
LENGTH = int(round(BARS * BAR * SR))

OUT = Path(__file__).resolve().parent.parent / "assets" / "maps" / "sounds"

# nivel final: parecido a la musica de ambiente del juego (mas bajo, relax)
TARGET_RMS_DB = -25.0

rng = np.random.default_rng(7)


def mtof(m):
    return 440.0 * 2.0 ** ((m - 69) / 12.0)


def tvec(dur):
    return np.arange(int(dur * SR)) / SR


def add(buf, start, sig, gain=1.0, pan=0.0):
    """Suma sig en buf (estereo) desde start segundos, dando la vuelta."""

    n = len(sig)
    i0 = int(start * SR) % LENGTH

    idx = (i0 + np.arange(n)) % LENGTH

    left = gain * np.sqrt(0.5 * (1.0 - pan))
    right = gain * np.sqrt(0.5 * (1.0 + pan))

    np.add.at(buf[0], idx, sig * left)
    np.add.at(buf[1], idx, sig * right)


def envelope(t, attack, tau, release_at=None, release=0.08):
    env = np.minimum(1.0, t / attack) * np.exp(-t / tau)

    if release_at is not None:
        tail = np.clip((release_at + release - t) / release, 0.0, 1.0)
        env *= tail

    return env


# ------------------------------------------------------------- instrumentos

def epiano(freq, dur, vel=1.0):
    """Piano electrico tipo Rhodes: cuerpo calido y un tintineo al atacar."""

    t = tvec(dur)

    tau = 1.9 if freq < 300 else 1.4 if freq < 600 else 0.9

    body = np.sin(2 * np.pi * freq * t)
    body += 0.30 * np.sin(2 * np.pi * freq * 2.0 * t) * np.exp(-t / 0.9)
    body += 0.12 * np.sin(2 * np.pi * freq * 3.0 * t) * np.exp(-t / 0.4)

    tine = 0.10 * np.sin(2 * np.pi * freq * 7.0 * t) * np.exp(-t / 0.07)

    trem = 1.0 + 0.05 * np.sin(2 * np.pi * 4.2 * t)

    sig = (body + tine) * trem

    return sig * envelope(t, 0.006, tau, release_at=dur - 0.15) * vel


def bass(freq, dur, vel=1.0):

    t = tvec(dur)

    sig = np.sin(2 * np.pi * freq * t) + 0.28 * np.sin(2 * np.pi * freq * 2 * t)

    return sig * envelope(t, 0.025, 1.8, release_at=dur - 0.12) * vel


def pad(freq, dur, vel=1.0):
    """Colchon suave: tres senos apenas desafinados con ataque lento."""

    t = tvec(dur)

    sig = np.zeros_like(t)

    for detune in (-0.0035, 0.0, 0.0035):
        sig += np.sin(2 * np.pi * freq * (1.0 + detune) * t + detune * 40)

    sig += 0.25 * np.sin(2 * np.pi * freq * 2.0 * t)

    rise = np.clip(t / 1.2, 0.0, 1.0) ** 2
    fall = np.clip((dur - t) / 1.4, 0.0, 1.0) ** 2

    return sig / 3.0 * rise * fall * vel


def kalimba(freq, dur=1.8, vel=1.0):
    """Campanita de pulgar: seno limpio con un armonico corto."""

    t = tvec(dur)

    sig = np.sin(2 * np.pi * freq * t)
    sig += 0.35 * np.sin(2 * np.pi * freq * 3.0 * t) * np.exp(-t / 0.10)
    sig += 0.10 * np.sin(2 * np.pi * freq * 5.4 * t) * np.exp(-t / 0.05)

    return sig * envelope(t, 0.003, 0.55, release_at=dur - 0.2) * vel


# ------------------------------------------------------------------ musica

# (nombre, notas del acorde en MIDI, bajo en MIDI)
FMAJ7 = ((53, 57, 60, 64), 41)
EM7 = ((52, 55, 59, 62), 40)
DM7 = ((50, 53, 57, 60), 38)
CMAJ7 = ((48, 52, 55, 59), 36)
G6 = ((55, 59, 62, 64), 43)
AM7 = ((57, 60, 64, 67), 45)
CMAJ9 = ((48, 52, 55, 59, 62), 36)

PROGRESSION = [
    FMAJ7, EM7, DM7, CMAJ7,
    FMAJ7, EM7, DM7, G6,
    AM7, DM7, G6, CMAJ7,
    FMAJ7, EM7, DM7, CMAJ9,
]

# pentatonica de Do para la campanita (queda bien sobre todos los acordes)
SCALE = [72, 74, 76, 79, 81, 84, 86]


def render_dry():

    buf = np.zeros((2, LENGTH))

    # --- acordes, bajo y colchon
    for bar, (chord, root) in enumerate(PROGRESSION):

        t0 = bar * BAR

        # piano: acorde arpegiado suave en el 1 y un golpecito en el "y" del 3
        for k, note in enumerate(chord):
            add(
                buf, t0 + k * 0.045,
                epiano(mtof(note), BEAT * 3.4, 0.62 - 0.03 * k),
                gain=0.34, pan=-0.18 + 0.12 * k
            )

        for k, note in enumerate(chord[1:]):
            add(
                buf, t0 + BEAT * 2.5 + k * 0.04,
                epiano(mtof(note + 12 if k == 2 else note), BEAT * 1.5, 0.40),
                gain=0.26, pan=0.05 + 0.1 * k
            )

        # bajo: la tonica larga y la quinta liviana en el 3
        add(buf, t0, bass(mtof(root), BEAT * 2.4, 1.0), gain=0.40)
        add(buf, t0 + BEAT * 2.0, bass(mtof(root + 7), BEAT * 1.9, 0.55),
            gain=0.30)

        # colchon
        for note in chord:
            add(
                buf, t0 - 0.25,
                pad(mtof(note), BAR + 0.7, 1.0),
                gain=0.045, pan=rng.uniform(-0.5, 0.5)
            )

    # --- campanita: frases cortitas y espaciadas, nunca en todos los compases
    pos = 3
    spots = [0.5, 1.5, 2.0, 2.5, 3.5]

    for bar in range(BARS):

        if bar % 4 == 0 or rng.random() < 0.30:
            continue

        count = int(rng.choice([2, 2, 3]))
        beats = sorted(rng.choice(spots, size=count, replace=False))

        for beat in beats:

            pos = int(np.clip(pos + rng.choice([-2, -1, -1, 0, 1, 1, 2]),
                              0, len(SCALE) - 1))

            add(
                buf, bar * BAR + beat * BEAT,
                kalimba(mtof(SCALE[pos] + (0 if pos else 12)), 1.8, 0.8),
                gain=0.11, pan=rng.uniform(-0.45, 0.45)
            )

    return buf


def reverb(buf, wet=0.30, decay=2.4):
    """Reverb circular (convolucion por FFT): la cola da la vuelta al loop."""

    n = int(decay * 1.2 * SR)
    t = np.arange(n) / SR

    out = np.zeros_like(buf)

    for ch in range(2):

        ir = rng.standard_normal(n) * np.exp(-t / (decay / 5.5))

        # sin brillo: la reverb suena a sala tapizada
        spec = np.fft.rfft(ir)
        freq = np.fft.rfftfreq(n, 1.0 / SR)
        ir = np.fft.irfft(spec / (1.0 + (freq / 2500.0) ** 2), n)

        ir /= np.sqrt(np.sum(ir ** 2))

        out[ch] = np.fft.irfft(
            np.fft.rfft(buf[ch]) * np.fft.rfft(ir, LENGTH), LENGTH
        )

    return buf * (1.0 - wet * 0.5) + out * wet


def warm(buf, cutoff=4200.0):
    """Quita el brillo (filtro suave en frecuencia, tambien circular)."""

    freq = np.fft.rfftfreq(LENGTH, 1.0 / SR)

    shape = 1.0 / (1.0 + (freq / cutoff) ** 2)

    # y saca el rumble de abajo
    shape *= 1.0 - 1.0 / (1.0 + (freq / 38.0) ** 2)

    return np.stack([np.fft.irfft(np.fft.rfft(c) * shape, LENGTH) for c in buf])


def main():

    buf = render_dry()
    buf = reverb(buf)
    buf = warm(buf)

    rms = np.sqrt(np.mean(buf ** 2))
    buf *= (10 ** (TARGET_RMS_DB / 20.0)) / rms

    peak = np.max(np.abs(buf))

    if peak > 0.55:
        buf *= 0.55 / peak

    pcm = (np.clip(buf, -1.0, 1.0).T * 32767).astype("<i2")

    OUT.mkdir(parents=True, exist_ok=True)

    wav_path = OUT / "tienda.wav"

    with wave.open(str(wav_path), "wb") as f:
        f.setnchannels(2)
        f.setsampwidth(2)
        f.setframerate(SR)
        f.writeframes(pcm.tobytes())

    print(f"{wav_path.name}: {LENGTH / SR:.1f} s")

    if shutil.which("ffmpeg"):

        ogg_path = OUT / "tienda.ogg"

        subprocess.run(
            ["ffmpeg", "-y", "-loglevel", "error", "-i", str(wav_path),
             "-c:a", "libvorbis", "-q:a", "4", str(ogg_path)],
            check=True
        )

        wav_path.unlink()

        print(f"{ogg_path.name} listo")


if __name__ == "__main__":
    main()