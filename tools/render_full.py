"""Resumable renderer/assembler for LUMEN episode 1.

Render one or more chunks, safely resume later, then concatenate and mux the
procedural soundtrack. This avoids losing an entire six-minute render if a dev
session stops halfway through.

Examples:
  python tools/render_full.py --fps 24 --chunk-seconds 15 --only 0
  python tools/render_full.py --fps 24 --chunk-seconds 15 --only 1 2 3
  python tools/render_full.py --fps 24 --chunk-seconds 15 --missing
  python tools/render_full.py --fps 24 --chunk-seconds 15 --assemble
"""
from __future__ import annotations

import argparse
import math
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import imageio_ffmpeg

from engine.cinematic import encode
from episodes.ep01_first_light import DURATION, frame_at


def chunk_bounds(index: int, seconds: float) -> tuple[float, float]:
    start = index * seconds
    return start, min(DURATION, start + seconds)


def chunk_path(folder: Path, index: int, fps: int) -> Path:
    return folder / f"ep01_{index:03d}_{fps}fps.mp4"


def valid_video(path: Path) -> bool:
    return path.exists() and path.stat().st_size > 4096


def render_chunk(index: int, seconds: float, fps: int, outdir: Path, preset: str, crf: int) -> Path:
    start, end = chunk_bounds(index, seconds)
    if start >= DURATION:
        raise ValueError(f"chunk {index} starts after episode end")
    out = chunk_path(outdir, index, fps)
    outdir.mkdir(parents=True, exist_ok=True)
    count = max(1, int(round((end - start) * fps)))

    def frames():
        for i in range(count):
            yield frame_at(start + i / fps)

    tmp = out.with_suffix(".partial.mp4")
    if tmp.exists():
        tmp.unlink()
    print(f"chunk {index}: {start:.1f}s–{end:.1f}s -> {out.name}", flush=True)
    encode(frames(), str(tmp), fps=fps, crf=crf, preset=preset)
    tmp.replace(out)
    return out


def ensure_audio() -> Path:
    audio = ROOT / "media" / "ep01.wav"
    if not audio.exists():
        subprocess.check_call([sys.executable, str(ROOT / "episodes" / "ep01_audio.py"), str(audio)])
    return audio


def assemble(seconds: float, fps: int, outdir: Path, output: Path) -> None:
    n = math.ceil(DURATION / seconds)
    chunks = [chunk_path(outdir, i, fps) for i in range(n)]
    missing = [p for p in chunks if not valid_video(p)]
    if missing:
        names = ", ".join(p.name for p in missing[:8])
        more = "…" if len(missing) > 8 else ""
        raise SystemExit(f"cannot assemble; {len(missing)} chunks missing: {names}{more}")

    manifest = outdir / "concat.txt"
    manifest.write_text("".join(f"file '{p.resolve().as_posix()}'\n" for p in chunks))
    silent = ROOT / "media" / "ep01_silent.mp4"
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    subprocess.check_call([
        ffmpeg, "-y", "-f", "concat", "-safe", "0", "-i", str(manifest),
        "-c", "copy", str(silent),
    ])
    audio = ensure_audio()
    output.parent.mkdir(parents=True, exist_ok=True)
    subprocess.check_call([
        ffmpeg, "-y", "-i", str(silent), "-i", str(audio),
        "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", "-shortest",
        "-movflags", "+faststart", str(output),
    ])
    print(output)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--fps", type=int, default=24)
    p.add_argument("--chunk-seconds", type=float, default=15.0)
    p.add_argument("--preset", default=os.environ.get("LUMEN_PRESET", "veryfast"))
    p.add_argument("--crf", type=int, default=19)
    p.add_argument("--only", type=int, nargs="*")
    p.add_argument("--missing", action="store_true")
    p.add_argument("--assemble", action="store_true")
    p.add_argument("--output", default=str(ROOT / "media" / "ep01_first_light.mp4"))
    args = p.parse_args()

    outdir = ROOT / "media" / "chunks"
    count = math.ceil(DURATION / args.chunk_seconds)
    if args.only is not None:
        indices = args.only
    elif args.missing:
        indices = [i for i in range(count) if not valid_video(chunk_path(outdir, i, args.fps))]
    else:
        indices = []

    for i in indices:
        if not 0 <= i < count:
            p.error(f"chunk index {i} out of range 0..{count-1}")
        path = chunk_path(outdir, i, args.fps)
        if valid_video(path):
            print(f"chunk {i}: already rendered, skipping")
            continue
        render_chunk(i, args.chunk_seconds, args.fps, outdir, args.preset, args.crf)

    if args.assemble:
        assemble(args.chunk_seconds, args.fps, outdir, Path(args.output))
    if not indices and not args.assemble:
        print(f"{count} chunks total; use --only, --missing, or --assemble")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
