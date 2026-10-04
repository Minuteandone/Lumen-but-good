"""Render a time range from Episode 1 without rendering the whole six-minute film.

Examples:
  python tools/render_segment.py 103 126 media/test_first_light.mp4 --fps 8
  python tools/render_segment.py 196 242 media/test_moth.mp4 --fps 12 --preset veryfast

This exists because development renders should be resumable instead of making one
six-minute render an all-or-nothing operation.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from engine.cinematic import encode
from episodes.ep01_first_light import DURATION, frame_at


def segment_frames(start: float, end: float, fps: int):
    count = max(1, int(round((end - start) * fps)))
    for i in range(count):
        yield frame_at(start + i / fps)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("start", type=float)
    p.add_argument("end", type=float)
    p.add_argument("output")
    p.add_argument("--fps", type=int, default=12)
    p.add_argument("--crf", type=int, default=21)
    p.add_argument("--preset", default="veryfast")
    args = p.parse_args()
    if not (0 <= args.start < args.end <= DURATION):
        p.error(f"range must satisfy 0 <= start < end <= {DURATION}")
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    encode(segment_frames(args.start, args.end, args.fps), str(out),
           fps=args.fps, crf=args.crf, preset=args.preset)
    print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
