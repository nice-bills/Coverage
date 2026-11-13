# Voiceover

Generated with Kokoro-82M (Apache-2.0, https://huggingface.co/hexgrad/Kokoro-82M), voice `af_heart`, by `voice.py`.
Each line is fitted inside its scene; the music is ducked under it and the mix is normalised to -14 LUFS.

| Start | Line |
|---|---|
| 0:00.3 | Dashboards say NEAR burns back under one percent of what it mints. |
| 0:05.2 | That number is right. It measures the wrong layer. |
| 0:10.3 | Count the Intents buybacks too, and twelve percent comes back. Break-even is eight times away, not a hundred and eight. |
| 0:18.4 | Coverage is a live report. Every number comes from NEAR mainnet. |
| 0:24.3 | One command. No keys, no network. It rebuilds every number, and prints a hash that matches the read-me. |
| 0:32.3 | Every epoch since February, read straight from block headers. |
| 0:39.3 | The chain got quieter. Intents didn't. Its activity nearly tripled. |
| 0:46.3 | Break-even turns on two votes: fee capture, and the issuance cut. Its veto window closes on the sixteenth. |
| 0:53.3 | Our forecasts were frozen in Bitcoin before the data existed. So far, every one is inside its range. |
| 1:01.2 | Our verdict: not yet a supply story. The bet is governance. |
| 1:07.4 | Coverage. Check every number yourself. |

Rebuild (Python 3.10 to 3.12 with `kokoro>=0.9.4`, `soundfile` and `espeak-ng`):

```
python voice.py af_heart        # out/voice.wav; try am_michael or bf_emma for other voices
ffmpeg -i out/score.wav -i out/voice.wav -filter_complex "[1:a]aresample=48000,pan=stereo|c0=c0|c1=c0,asplit=2[v][sc];[0:a]volume=0.55[m];[m][sc]sidechaincompress=threshold=0.02:ratio=8:attack=20:release=400[duck];[duck][v]amix=inputs=2:duration=first:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=11[a]" -map "[a]" -ar 48000 out/mix.wav
ffmpeg -i out/frames.mp4 -i out/mix.wav -c:v copy -c:a aac -b:a 192k -shortest -movflags +faststart out/coverage-demo-voice.mp4
```

Your own voice instead: record over the same timings and swap it in for out/voice.wav.
