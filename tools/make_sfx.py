"""Генератор звуковых эффектов «Золотого рейда».

Эффекты синтезируются прямо здесь, поэтому у них нет чужих авторских прав.
Скрипт не нужен в сборке APK, но хранится в репозитории, чтобы результат
всегда можно было пересоздать:

    python tools/make_sfx.py

На выходе — короткие WAV-файлы в game/assets/sfx/.
"""

from __future__ import annotations

import math
import random
import struct
import wave
from pathlib import Path

SAMPLE_RATE = 22050
OUT_DIR = Path(__file__).resolve().parent.parent / "game" / "assets" / "sfx"


def midi_to_freq(note: float) -> float:
    return 440.0 * (2.0 ** ((note - 69.0) / 12.0))


def _blank(seconds: float) -> list[float]:
    return [0.0] * (int(seconds * SAMPLE_RATE) + 1)


def _add_tone(buf, start, duration, freq, amp, partials=(1.0,), decay=6.0,
              sweep=0.0, attack=0.005):
    """Добавляет затухающий тон. ``sweep`` — скольжение частоты за секунду."""
    n0 = int(start * SAMPLE_RATE)
    if n0 >= len(buf):
        return
    n = min(int(duration * SAMPLE_RATE), len(buf) - n0)
    att = max(1, int(attack * SAMPLE_RATE))
    phase = 0.0
    mult = 1.0 + sweep
    for i in range(n):
        f = freq * (mult ** (i / SAMPLE_RATE))
        phase += 2.0 * math.pi * f / SAMPLE_RATE
        env = amp * math.exp(-decay * (i / SAMPLE_RATE))
        if i < att:
            env *= i / att
        value = 0.0
        for index, weight in enumerate(partials, start=1):
            value += weight * math.sin(phase * index)
        buf[n0 + i] += env * value


def _add_noise(buf, start, duration, amp, decay=30.0, low=False, rng=None):
    n0 = int(start * SAMPLE_RATE)
    if n0 >= len(buf):
        return
    n = min(int(duration * SAMPLE_RATE), len(buf) - n0)
    if rng is None:
        rng = random.Random(7)
    prev = 0.0
    for i in range(n):
        noise = rng.uniform(-1.0, 1.0)
        if low:
            # Грубый «лоупасс»: скользящее среднее.
            sample = (noise + prev) * 0.5
            prev = noise
        else:
            sample = noise - prev  # грубый «хайпасс»
            prev = noise
        env = amp * math.exp(-decay * (i / SAMPLE_RATE))
        buf[n0 + i] += env * sample


def make_click() -> list[float]:
    buf = _blank(0.07)
    _add_tone(buf, 0.0, 0.06, 1180.0, 0.5, partials=(1.0, 0.3), decay=45.0, sweep=-0.12)
    return buf


def make_build() -> list[float]:
    buf = _blank(0.24)
    _add_noise(buf, 0.0, 0.05, 0.5, decay=90.0)
    _add_tone(buf, 0.02, 0.20, 150.0, 0.5, partials=(1.0, 0.4), decay=16.0)
    _add_tone(buf, 0.06, 0.16, midi_to_freq(76), 0.30, partials=(1.0, 0.5, 0.2), decay=22.0)
    return buf


def make_shoot() -> list[float]:
    buf = _blank(0.12)
    _add_tone(buf, 0.0, 0.10, 900.0, 0.35, partials=(1.0, 0.2), decay=30.0, sweep=-0.55)
    _add_noise(buf, 0.0, 0.05, 0.18, decay=70.0)
    return buf


def make_hit() -> list[float]:
    buf = _blank(0.22)
    _add_tone(buf, 0.0, 0.20, 96.0, 0.55, partials=(1.0, 0.35), decay=14.0, sweep=-0.2)
    _add_noise(buf, 0.0, 0.09, 0.28, decay=45.0, low=True)
    return buf


def make_coin() -> list[float]:
    buf = _blank(0.24)
    _add_tone(buf, 0.0, 0.12, midi_to_freq(88), 0.40, partials=(1.0, 0.4, 0.2), decay=20.0)
    _add_tone(buf, 0.07, 0.16, midi_to_freq(93), 0.34, partials=(1.0, 0.4, 0.2), decay=18.0)
    return buf


def make_wave() -> list[float]:
    buf = _blank(0.55)
    for offset, note in ((0.0, 62), (0.16, 66), (0.32, 69)):
        _add_tone(buf, offset, 0.30, midi_to_freq(note), 0.34,
                  partials=(1.0, 0.5, 0.25), decay=6.0, attack=0.02)
    return buf


def make_win() -> list[float]:
    buf = _blank(0.95)
    for k, note in enumerate((60, 64, 67, 72)):
        _add_tone(buf, k * 0.14, 0.55 - k * 0.05, midi_to_freq(note), 0.36,
                  partials=(1.0, 0.45, 0.2), decay=5.0, attack=0.01)
    return buf


def make_lose() -> list[float]:
    buf = _blank(0.95)
    for k, note in enumerate((67, 64, 60, 55)):
        _add_tone(buf, k * 0.15, 0.60 - k * 0.05, midi_to_freq(note), 0.36,
                  partials=(1.0, 0.5, 0.25), decay=4.5, attack=0.01)
    return buf


BUILDERS = {
    "click": make_click,
    "build": make_build,
    "shoot": make_shoot,
    "hit": make_hit,
    "coin": make_coin,
    "wave": make_wave,
    "win": make_win,
    "lose": make_lose,
}


def normalize(buf: list[float], peak: float = 0.85) -> list[float]:
    top = max((abs(v) for v in buf), default=0.0)
    if top <= 1e-6:
        return buf
    scale = peak / top
    return [v * scale for v in buf]


def write_wav(path: Path, buf: list[float]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frames = bytearray()
    for value in buf:
        clipped = -1.0 if value < -1.0 else 1.0 if value > 1.0 else value
        frames += struct.pack("<h", int(clipped * 32767))
    with wave.open(str(path), "wb") as fh:
        fh.setnchannels(1)
        fh.setsampwidth(2)
        fh.setframerate(SAMPLE_RATE)
        fh.writeframes(bytes(frames))


def main() -> None:
    for name, builder in BUILDERS.items():
        buf = normalize(builder())
        path = OUT_DIR / f"sfx_{name}.wav"
        write_wav(path, buf)
        ms = len(buf) / SAMPLE_RATE * 1000
        print(f"{path.name:<16} {ms:6.0f} мс  {len(buf) * 2 / 1024:6.1f} КБ")


if __name__ == "__main__":
    main()
