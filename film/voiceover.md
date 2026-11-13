# Voiceover (optional; the captions carry the film on mute)

Read at a calm pace. Each line starts at the time shown and must end before the next.

| Start | Say |
|---|---|
| 0:00 | "Every NEAR fee-burn dashboard says the same thing: NEAR burns back under one percent of what it mints." |
| 0:05 | "That number is right. It measures the wrong layer." |
| 0:10 | "Since April, NEAR Intents has sent about ten thousand NEAR a day to a buyback account. Count it, and NEAR wins back twelve percent. Break-even is eight times away, not a hundred and eight." |
| 0:18 | "Coverage is a live research report. Every number comes from NEAR mainnet." |
| 0:24 | "One command, no keys, no network. It rebuilds every number in two seconds and prints a hash that must match the README." |
| 0:32 | "Every epoch since February, read from block headers, exact to the yoctoNEAR." |
| 0:39 | "BigQuery shows the chain got quieter. Intents didn't: its activity grew almost three times." |
| 0:46 | "Break-even turns on two votes: how much of the Intents fees go to buybacks, and HSP-029, whose veto window closes on the sixteenth." |
| 0:53 | "Our forecasts were frozen in Bitcoin before the data existed. So far they're inside every range, and they close while you judge." |
| 1:01 | "Our verdict: not yet a supply story. The bet is governance." |
| 1:07 | "Coverage. Check every number yourself." |

Record it over film/out/coverage-demo.mp4 in any editor, or replace the score:
`ffmpeg -i film/out/frames.mp4 -i voice.m4a -i film/out/score.wav -filter_complex "[2]volume=0.35[m];[1][m]amix=inputs=2:duration=first[a]" -map 0:v -map "[a]" -c:v copy -c:a aac -shortest coverage-demo-vo.mp4`
