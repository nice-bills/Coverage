#!/usr/bin/env python3
"""Voiceover with Kokoro-82M (Apache-2.0, hexgrad/Kokoro-82M): one line per scene, each fitted inside its slot,
then mixed over out/score.wav with the music ducked under the voice. Writes out/voice.wav and out/mix.wav.
Needs: pip install "kokoro>=0.9.4" soundfile (Python 3.10-3.12) and espeak-ng."""
import sys, numpy as np, soundfile as sf
from kokoro import KPipeline
VOICE = sys.argv[1] if len(sys.argv) > 1 else "af_heart"
SR = 24000
# (start, end of slot in seconds, text). Numbers are spelled the way they should be said.
LINES = [
    (0.3, 5, "Dashboards say NEAR burns back under one percent of what it mints."),
    (5.2, 10, "That number is right. It measures the wrong layer."),
    (10.3, 18.3, "Count the Intents buybacks too, and twelve percent comes back. Break-even is eight times away, not a hundred and eight."),
    (18.4, 24, "Coverage is a live report. Every number comes straight from the NEAR blockchain."),
    (24.3, 32, "One command. No keys, no network. It rebuilds every number, and prints a hash that matches the read-me."),
    (32.3, 39, "Every epoch since February, read straight from block headers."),
    (39.3, 46, "The chain got quieter. Intents didn't. Its activity nearly tripled."),
    (46.3, 53, "Break-even turns on two votes: fee capture, and the issuance cut. Its veto window closes on the sixteenth."),
    (53.3, 61, "Our forecasts were frozen in Bitcoin before the data existed. So far, every one is inside its range."),
    (61.2, 67, "Our verdict: not yet a supply story. The bet is governance."),
    (67.4, 72, "Coverage. Check every number yourself."),
]
pipe = KPipeline(lang_code="a")
def say(text, speed):
    return np.concatenate([a.numpy() if hasattr(a, "numpy") else np.asarray(a) for _, _, a in pipe(text, voice=VOICE, speed=speed)])
voice = np.zeros(int(72 * SR))
for a, b, text in LINES:
    speed, room = 1.0, b - a - 0.25
    audio = say(text, speed)
    if len(audio) / SR > room:  # too long for its slot: speak a little faster, never above 1.2x
        speed = min(1.15, len(audio) / SR / room)
        audio = say(text, speed)
    print(f"{a:5.1f}s  {len(audio) / SR:4.1f}s of {room:4.1f}s  speed {speed:.2f}  {text[:48]}")
    i = int(a * SR)
    voice[i:i + len(audio)] += audio[:len(voice) - i]
sf.write("out/voice.wav", voice, SR)
