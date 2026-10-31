"""Генератор фоновой музыки «Золотого рейда».

Мелодии синтезируются прямо здесь (аддитивный синтез), поэтому у них нет
чужих авторских прав — музыка наша. Скрипт не нужен в сборке APK, но
хранится в репозитории, чтобы результат всегда можно было пересоздать:

    python tools/make_music.py

На выходе — короткие зацикленные WAV-файлы в game/assets/music/.
"""

from __future__ import annotations

import math
import random
import struct
import wave
from pathlib import Path

SAMPLE_RATE = 16000
OUT_DIR = Path(__file__).resolve().parent.parent / "game" / "assets" / "music"


def midi_to_freq(note: float) -> float:
    return 440.0 * (2.0 ** ((note - 69.0) / 12.0))


# ---------------------------------------------------------------------------
# Темы: аккордовая петля, темп, характер звука.
# ---------------------------------------------------------------------------
THEMES = {
    # Главное меню: спокойная «ночная» тема, редкие колокольчики.
    "menu": dict(
        bpm=66, bars=8, root=57, prog=[[57, 60, 64], [53, 57, 60],
                                       [48, 52, 55], [55, 59, 62]],
        pad=0.16, pad_high=0.07, bass=0.12, arp=0.10, perc=0.0,
        arp_notes=[12, 16, 19, 24, 19, 16], shimmer=0.05, seed=11,
    ),
    # Зелёные земли: тёплая светлая тема.
    "green": dict(
        bpm=84, bars=8, root=60, prog=[[48, 55, 64], [55, 59, 62],
                                       [57, 60, 64], [53, 57, 60]],
        pad=0.15, pad_high=0.09, bass=0.11, arp=0.12, perc=0.05,
        arp_notes=[12, 16, 19, 24, 19, 16], shimmer=0.03, seed=22,
    ),
    # Каменный перевал: чуть мрачнее, размеренный шаг.
    "stone": dict(
        bpm=80, bars=8, root=50, prog=[[50, 53, 57], [46, 50, 53],
                                       [53, 57, 60], [48, 52, 55]],
        pad=0.16, pad_high=0.06, bass=0.14, arp=0.09, perc=0.06,
        arp_notes=[12, 15, 19, 22, 19, 15], shimmer=0.02, seed=33,
    ),
    # Пепельная пустошь: низкий гул и редкие удары.
    "ash": dict(
        bpm=74, bars=8, root=52, prog=[[52, 55, 59], [48, 52, 55],
                                       [55, 59, 62], [50, 54, 57]],
        pad=0.18, pad_high=0.05, bass=0.16, arp=0.07, perc=0.09,
        arp_notes=[12, 15, 19, 15], shimmer=0.02, seed=44,
    ),
    # Студёная теснина: высокие холодные «стёкла».
    "frost": dict(
        bpm=70, bars=8, root=59, prog=[[59, 62, 66], [55, 59, 62],
                                       [50, 54, 57], [57, 61, 64]],
        pad=0.13, pad_high=0.10, bass=0.10, arp=0.11, perc=0.03,
        arp_notes=[12, 19, 24, 26, 24, 19], shimmer=0.09, seed=55,
    ),
    # Пылающий кратер: напор, быстрый арпеджио и барабаны.
    "ember": dict(
        bpm=94, bars=8, root=57, prog=[[57, 60, 64], [55, 59, 62],
                                       [53, 57, 60], [52, 56, 59]],
        pad=0.15, pad_high=0.07, bass=0.15, arp=0.13, perc=0.12,
        arp_notes=[12, 15, 19, 24, 19, 15], shimmer=0.04, seed=66,
    ),
}


def _add_note(buf, start, duration, freq, amp, partials=(1.0,), attack=0.4,
              release=0.5, pluck=False, detune=0.0, rng=None):
    """Добавляет в буфер (список float) одну ноту."""
    total = len(buf)
    n0 = int(start * SAMPLE_RATE)
    if n0 >= total:
        return
    n = min(int(duration * SAMPLE_RATE), total - n0)
    if n <= 0:
        return
    att = max(1, int(attack * SAMPLE_RATE))
    rel = max(1, int(release * SAMPLE_RATE))
    voices = []
    for index, weight in enumerate(partials, start=1):
        f = freq * index
        if detune and rng is not None:
            f *= 1.0 + rng.uniform(-detune, detune)
        voices.append((2.0 * math.pi * f / SAMPLE_RATE, weight))
    if pluck:
        decay = math.exp(-1.0 / (max(0.04, duration) * SAMPLE_RATE) * 4.0)
    local = buf
    for i in range(n):
        if pluck:
            env = amp
            amp *= decay
        elif i < att:
            env = amp * (i / att)
        elif i > n - rel:
            env = amp * max(0.0, (n - i) / rel)
        else:
            env = amp
        value = 0.0
        for phase, weight in voices:
            value += weight * math.sin(phase * i)
        local[n0 + i] += env * value


def _add_kick(buf, start, amp=0.5):
    total = len(buf)
    n0 = int(start * SAMPLE_RATE)
    if n0 >= total:
        return
    dur = 0.16
    n = min(int(dur * SAMPLE_RATE), total - n0)
    for i in range(n):
        t = i / SAMPLE_RATE
        freq = 46.0 + 70.0 * math.exp(-t * 34.0)
        env = amp * math.exp(-t * 24.0)
        buf[n0 + i] += env * math.sin(2.0 * math.pi * freq * t)


def _add_hat(buf, start, amp=0.16, rng=None):
    total = len(buf)
    n0 = int(start * SAMPLE_RATE)
    if n0 >= total:
        return
    dur = 0.06
    n = min(int(dur * SAMPLE_RATE), total - n0)
    if rng is None:
        rng = random.Random(1)
    prev = 0.0
    for i in range(n):
        t = i / SAMPLE_RATE
        noise = rng.uniform(-1.0, 1.0)
        high = noise - prev  # грубый «хайпасс»
        prev = noise
        env = amp * math.exp(-t * 70.0)
        buf[n0 + i] += env * high * 0.5


def build_theme(name: str, cfg: dict) -> list[float]:
    bpm = cfg["bpm"]
    beats_per_bar = 4
    bars = cfg["bars"]
    beat = 60.0 / bpm
    bar = beat * beats_per_bar
    length = bars * bar
    total = int(length * SAMPLE_RATE) + 1
    buf = [0.0] * total
    prog = cfg["prog"]
    rng = random.Random(cfg["seed"])

    for b in range(bars):
        chord = prog[b % len(prog)]
        t0 = b * bar
        # Пэд: аккорд держится весь такт с мягкой атакой и затуханием.
        for note in chord:
            _add_note(buf, t0, bar + 0.25, midi_to_freq(note), cfg["pad"],
                      partials=(1.0, 0.35, 0.14), attack=0.7 * bar,
                      release=0.45 * bar, detune=0.0025, rng=rng)
            _add_note(buf, t0, bar + 0.2, midi_to_freq(note + 12),
                      cfg["pad_high"], partials=(1.0, 0.22),
                      attack=0.8 * bar, release=0.4 * bar)
        # Бас — корень на октаву ниже.
        _add_note(buf, t0, bar, midi_to_freq(chord[0] - 12), cfg["bass"],
                  partials=(1.0, 0.4), attack=0.05, release=0.2 * bar)
        # Арпеджио/колокольчики.
        notes = cfg["arp_notes"]
        steps = max(1, len(notes))
        step = bar / steps
        for k, offset in enumerate(notes):
            note = chord[k % len(chord)] + offset
            _add_note(buf, t0 + k * step, duration=max(0.12, step * 1.1),
                      freq=midi_to_freq(note), amp=cfg["arp"],
                      partials=(1.0, 0.5, 0.2), pluck=True)
        # Лёгкая «стеклянная» искра.
        if cfg["shimmer"] > 0:
            top = max(chord) + 24
            _add_note(buf, t0 + bar * 0.5, bar * 0.5,
                      midi_to_freq(top), cfg["shimmer"],
                      partials=(1.0,), attack=bar * 0.2, release=bar * 0.3)
        # Барабаны.
        if cfg["perc"] > 0:
            _add_kick(buf, t0, cfg["perc"] * 4.2)
            _add_kick(buf, t0 + bar * 0.5, cfg["perc"] * 3.0)
            _add_hat(buf, t0 + beat, cfg["perc"] * 1.1, rng)
            _add_hat(buf, t0 + beat * 3, cfg["perc"] * 1.0, rng)

    # Мягкие края: зацикливание без щелчка.
    fade = int(0.02 * SAMPLE_RATE)
    for i in range(fade):
        gain = i / fade
        buf[i] *= gain
        buf[total - 1 - i] *= gain
    return buf


def normalize(buf: list[float], peak: float = 0.82) -> list[float]:
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
    for name, cfg in THEMES.items():
        buf = build_theme(name, cfg)
        buf = normalize(buf)
        path = OUT_DIR / f"theme_{name}.wav"
        write_wav(path, buf)
        seconds = len(buf) / SAMPLE_RATE
        print(f"{path.name:<20} {seconds:5.1f} с  {len(buf) * 2 / 1024:7.0f} КБ")


if __name__ == "__main__":
    main()
