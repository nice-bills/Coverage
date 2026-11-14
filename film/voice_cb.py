#!/usr/bin/env python3
"""Voiceover with Chatterbox (Resemble AI, MIT licence): more natural prosody than Kokoro. Same timed lines as voice.py;
a line longer than its slot is time-stretched by at most 12% (ffmpeg atempo keeps the pitch). Writes out/voice.wav.
Needs Python 3.11 with chatterbox-tts. Optional: python voice_cb.py ref.wav  (a 10 s clip of a voice to match)."""
import os, subprocess, sys, tempfile, numpy as np, soundfile as sf, torch
from chatterbox.tts import ChatterboxTTS
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import importlib.util
spec = importlib.util.spec_from_file_location("v", os.path.join(os.path.dirname(os.path.abspath(__file__)), "voice.py"))
src = open(spec.origin).read()
LINES = eval(src[src.index("LINES = [") + 8: src.index("]\n", src.index("LINES = [")) + 1])
torch.manual_seed(7)
model = ChatterboxTTS.from_pretrained(device="cpu")
SR = model.sr
ref = sys.argv[1] if len(sys.argv) > 1 else None
voice = np.zeros(int(72 * SR))
for a, b, text in LINES:
    wav = model.generate(text, audio_prompt_path=ref, exaggeration=0.45, cfg_weight=0.45, temperature=0.7).squeeze().numpy()
    # trim leading/trailing silence
    nz = np.where(np.abs(wav) > 0.01)[0]
    wav = wav[max(0, nz[0] - int(0.03 * SR)): nz[-1] + int(0.08 * SR)] if len(nz) else wav
    room = b - a - 0.2
    if len(wav) / SR > room:
        f = min(1.12, len(wav) / SR / room)
        with tempfile.TemporaryDirectory() as d:
            sf.write(f"{d}/i.wav", wav, SR)
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", f"{d}/i.wav", "-af", f"atempo={f:.3f}", f"{d}/o.wav"], check=True)
            wav, _ = sf.read(f"{d}/o.wav")
    print(f"{a:5.1f}s  {len(wav) / SR:4.1f}s of {room:4.1f}s  {text[:50]}", flush=True)
    i = int(a * SR)
    voice[i:i + len(wav)] += wav[:len(voice) - i]
sf.write("out/voice.wav", voice, SR)
