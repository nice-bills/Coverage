#!/usr/bin/env python3
"""Synthesize the score on the film's clock: a soft pad that changes chord at every scene, a tick on each cut,
a low swell into the reveal. Writes out/score.wav (48 kHz stereo), loudness about -14 LUFS (RMS approximation)."""
import numpy as np, wave
SR, DUR = 48000, 72.0
cuts = [0, 5, 10, 18, 24, 32, 39, 46, 53, 61, 67]
t = np.arange(int(SR * DUR)) / SR
out = np.zeros((len(t), 2))
hz = lambda n: 440 * 2 ** ((n - 69) / 12)
# A minor-ish to C major as the story turns: hook/problem minor, reveal onwards brighter, verdict and close resolve
chords = [[57, 60, 64], [53, 57, 60], [60, 64, 67], [55, 59, 62], [57, 60, 64], [53, 57, 62], [60, 64, 67],
          [55, 59, 64], [57, 62, 65], [53, 57, 60], [60, 64, 67, 72]]
for i, a in enumerate(cuts):
    b = cuts[i + 1] if i + 1 < len(cuts) else DUR
    m = (t >= a - 0.4) & (t < b + 0.8)
    tt = t[m] - (a - 0.4)
    env = np.minimum(1, tt / 0.9) * np.minimum(1, np.maximum(0, (b + 0.8 - t[m]) / 1.2))
    for k, n in enumerate(chords[i]):
        f = hz(n)
        for det, ch in ((-0.15, 0), (0.15, 1)):  # slight detune, spread left and right
            out[m, ch] += env * 0.055 * (np.sin(2 * np.pi * (f + det) * t[m]) + 0.25 * np.sin(2 * np.pi * 2 * f * t[m]))
    # bass note
    out[m, :] += (env * 0.07 * np.sin(2 * np.pi * hz(chords[i][0] - 12) * t[m]))[:, None]
# tick on each cut (and a softer one on caption entries is left out: the cut is the beat)
for a in cuts[1:]:
    m = (t >= a) & (t < a + 0.12)
    tt = t[m] - a
    out[m, :] += (0.35 * np.exp(-tt * 60) * np.sin(2 * np.pi * 1900 * tt))[:, None]
# swell of filtered noise into the reveal (10 s) and into the verdict (61 s)
rng = np.random.default_rng(7)  # seeded: same file every run
for a in (10, 61):
    m = (t >= a - 1.6) & (t < a + 0.2)
    tt = t[m] - (a - 1.6)
    n = rng.standard_normal(m.sum())
    n = np.convolve(n, np.ones(40) / 40, mode="same")
    out[m, :] += (0.5 * (tt / 1.6) ** 2 * n)[:, None]
# fade in and out, then loudness: RMS to about -16 dBFS (about -14 LUFS for this material), peaks below -1 dBFS
out *= np.minimum(1, t / 0.5)[:, None] * np.minimum(1, (DUR - t) / 1.5)[:, None]
rms = np.sqrt(np.mean(out ** 2))
out *= 10 ** (-16 / 20) / rms
pk = np.max(np.abs(out))
if pk > 10 ** (-1 / 20):
    out = np.tanh(out / pk * 1.2) * 10 ** (-1 / 20) / np.tanh(1.2)
pcm = (out * 32767).astype("<i2")
with wave.open("out/score.wav", "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
print("score.wav", len(t) / SR, "s")
