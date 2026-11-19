"""Generate small, original WAV assets for the scene's optional audio."""

import math
import random
import struct
import wave
from pathlib import Path


SAMPLE_RATE = 22050
ROOT = Path(__file__).resolve().parents[1]
ASSET_DIR = ROOT / "assets"


def _envelope(position, duration, attack=0.16, release=0.48):
    return min(1.0, position / attack, max(0.0, duration - position) / release)


def _tone(frequency, position, harmonics=(1.0, 0.24, 0.08)):
    phase = 2.0 * math.pi * frequency * position
    return sum(amplitude * math.sin(index * phase) for index, amplitude in enumerate(harmonics, start=1))


def write_music(path):
    duration = 16.0
    samples = int(SAMPLE_RATE * duration)
    random_source = random.Random(31420)
    chords = (
        (130.81, 196.00, 261.63, 329.63),
        (110.00, 164.81, 220.00, 293.66),
        (146.83, 220.00, 293.66, 349.23),
        (98.00, 146.83, 196.00, 261.63),
    )
    melody = (
        (0.4, 587.33), (1.6, 523.25), (2.7, 440.00), (4.1, 493.88),
        (5.5, 587.33), (6.8, 659.25), (8.5, 587.33), (9.7, 493.88),
        (11.1, 440.00), (12.5, 392.00), (14.0, 440.00), (15.0, 493.88),
    )
    bird_calls = ((3.2, 0.22), (7.7, 0.28), (12.0, 0.20))
    noise = 0.0
    output = bytearray()

    for sample_index in range(samples):
        time = sample_index / SAMPLE_RATE
        chord = chords[int(time // 4) % len(chords)]
        value = 0.0
        for note_index, frequency in enumerate(chord):
            value += _tone(frequency, time, (1.0, 0.12, 0.025)) * (0.045 / (note_index + 1))

        for start, frequency in melody:
            local_time = time - start
            if 0 <= local_time < 0.72:
                envelope = _envelope(local_time, 0.72, 0.025, 0.42)
                value += _tone(frequency, local_time, (1.0, 0.3, 0.07)) * 0.12 * envelope

        for start, length in bird_calls:
            local_time = time - start
            if 0 <= local_time < length:
                glide = 1280.0 + 850.0 * math.sin(math.pi * local_time / length)
                value += math.sin(2.0 * math.pi * glide * local_time) * 0.035 * _envelope(local_time, length, 0.015, 0.07)

        noise = noise * 0.985 + random_source.uniform(-1.0, 1.0) * 0.015
        value += noise * 0.018

        edge = min(1.0, time / 0.45, (duration - time) / 0.45)
        value *= max(0.0, edge)
        output.extend(struct.pack("<h", int(max(-1.0, min(1.0, value)) * 32767)))

    with wave.open(str(path), "wb") as audio_file:
        audio_file.setnchannels(1)
        audio_file.setsampwidth(2)
        audio_file.setframerate(SAMPLE_RATE)
        audio_file.writeframes(output)


def write_click(path):
    duration = 0.055
    samples = int(SAMPLE_RATE * duration)
    output = bytearray()
    for sample_index in range(samples):
        time = sample_index / SAMPLE_RATE
        envelope = math.exp(-time * 70.0)
        frequency = 1550.0 - 570.0 * time / duration
        value = math.sin(2.0 * math.pi * frequency * time) * envelope * 0.28
        output.extend(struct.pack("<h", int(value * 32767)))

    with wave.open(str(path), "wb") as audio_file:
        audio_file.setnchannels(1)
        audio_file.setsampwidth(2)
        audio_file.setframerate(SAMPLE_RATE)
        audio_file.writeframes(output)


def main():
    ASSET_DIR.mkdir(parents=True, exist_ok=True)
    write_music(ASSET_DIR / "nature_loop.wav")
    write_click(ASSET_DIR / "button_tap.wav")


if __name__ == "__main__":
    main()
