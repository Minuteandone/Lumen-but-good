# LUMEN — cinematic remake

A slower, more cinematic remake of **LUMEN**, the wordless animated series about a tiny lantern robot waking up in a dead space station.

For now this repository contains **Episode 1 only**.

## Episode 1 — First Light

Lumen boots up alone in an abandoned, dark, dusty station. While exploring, he accidentally knocks a dead lamp back to life and realizes the room can still be restored. As he wakes the lights one by one, a tiny moth appears and lands on his back. Lumen panics; the moth panics because Lumen is panicking; eventually they both realize neither of them is a threat. Together they restore the first chamber until it looks almost new.

Then they discover the chamber was only the beginning.

Approximate runtime: **6m 18s**. No dialogue.

## Render

```bash
python3 episodes/ep01_first_light.py stills 12 34 108 185 222 275 326 351 366
python3 episodes/ep01_audio.py media/ep01.wav
python3 episodes/ep01_first_light.py render media/ep01_silent.mp4
ffmpeg -y -i media/ep01_silent.mp4 -i media/ep01.wav \
  -c:v copy -c:a aac -b:a 160k -shortest media/ep01_first_light.mp4
```

The renderer defaults to 960×540 at 24 fps. Set `LUMEN_SCALE=2` for supersampled output.

## Structure

- `engine/cinematic.py` — drawing, camera, lighting, dust and character helpers
- `engine/audio.py` — lightweight procedural audio helpers
- `episodes/ep01_first_light.py` — Episode 1 animation/timeline
- `episodes/ep01_audio.py` — Episode 1 soundscape and score
- `stills/` — optional rendered development frames
- `media/` — local rendered outputs (ignored by git except placeholders)


## Resumable render

For the full episode, the chunked renderer is safer than one six-minute render:

```bash
python tools/render_full.py --fps 24 --chunk-seconds 15 --missing
python tools/render_full.py --fps 24 --chunk-seconds 15 --assemble
```

For quick scene checks:

```bash
python tools/render_segment.py 196 242 media/test_moth.mp4 --fps 12 --preset veryfast
```

The finished development cut was assembled at 960×540 / 12 fps from time-contiguous chunks; the source still defaults to 24 fps for a smoother final-quality re-render.
