"""LUMEN — Episode 1: First Light (cinematic remake).

A wordless six-minute short. The story starts inside the abandoned station:
Lumen wakes, cleans the dust off himself, accidentally restores the first light,
meets a frightened little moth, and together they make one maintenance chamber
feel alive again — before discovering how impossibly huge the rest of the station is.
"""
from __future__ import annotations

import math
import os
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from engine.cinematic import (  # noqa: E402
    W, H, FPS, Camera, add_letterbox, apply_lighting, clamp, draw_ceiling_light,
    draw_dust, draw_far_station, draw_floor_lamp, draw_lumen, draw_moth,
    draw_station_room, draw_switch, encode, kf, make_canvas, make_emissive,
    smooth, smoother,
)

DURATION = 378.0  # 6:18 including end card
GROUND = 430
LAMP_X = 245
LIGHT_XS = [-430, -140, 160, 460, 760, 1060, 1360, 1620]
SWITCH_X = 570


def q(t: float, a: float, b: float) -> float:
    return smooth((t - a) / (b - a))


def qq(t: float, a: float, b: float) -> float:
    return smoother((t - a) / (b - a))


def blink(t: float, start: float, dur: float = 0.16) -> float:
    return 0.0 if start <= t < start + dur else 1.0


def title_card(t: float) -> Image.Image:
    img = make_canvas((2, 3, 7))
    d = ImageDraw.Draw(img)
    from engine.cinematic import font

    u = clamp((t - 371.0) / 1.3)
    v = clamp((378.0 - t) / 1.0)
    alpha = int(255 * min(u, v))
    glow = Image.new("RGBA", img.size, (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse([W * .28, H * .22, W * .72, H * .76], fill=(70, 185, 225, int(22 * min(u, v))))
    glow = glow.filter(ImageFilter.GaussianBlur(40))
    img.paste(glow, (0, 0), glow)

    f1 = font(58)
    f2 = font(19)
    text = "LUMEN"
    bbox = d.textbbox((0, 0), text, font=f1)
    x = (W - (bbox[2] - bbox[0])) / 2
    d.text((x, 214), text, font=f1, fill=(205, 244, 255, alpha))
    sub = "EPISODE 1  ·  FIRST LIGHT"
    bbox = d.textbbox((0, 0), sub, font=f2)
    x = (W - (bbox[2] - bbox[0])) / 2
    d.text((x, 288), sub, font=f2, fill=(142, 164, 181, alpha))
    return img


def frame_at(t: float) -> Image.Image:
    if t >= 371.0:
        return title_card(t)

    img = make_canvas()
    em = make_emissive()

    # 0:00–0:52 — BOOT. Start in the station, as requested: no exterior.
    if t < 52:
        cam = Camera(
            x=kf(t, [(0, -250), (18, -220), (39, -205), (52, -150)]),
            y=kf(t, [(0, 292), (22, 282), (52, 270)]),
            zoom=kf(t, [(0, 1.55), (15, 1.32), (52, 1.06)]),
        )
        draw_station_room(img, cam, clean=0, awake=0)
        bulb = kf(t, [(0, 0), (7.0, 0), (7.25, .20), (7.5, 0), (10.2, 0),
                      (10.5, .35), (11.1, .08), (13.5, .55), (18, .68), (52, .78)])
        eye = kf(t, [(0, 0), (5.7, 0), (5.9, .7), (6.05, 0), (9.1, 0),
                     (9.35, .9), (9.7, .15), (12.7, .4), (14.2, 1)])
        head_tilt = kf(t, [(0, -12), (14, -12), (22, 0), (30, 7), (35, -6), (52, 0)])
        dust = kf(t, [(0, 1), (26, 1), (33, .88), (38, .82), (44, .12), (52, .04)])
        mood = "tired" if t < 19 else "neutral"
        shake = 0.0
        squash = 1.0
        if 36.2 <= t <= 43.5:
            amp = 7.0 * math.sin(math.pi * clamp((t - 36.2) / 7.3))
            shake = math.sin(t * 31) * amp
            squash = .94 + .07 * math.sin(t * 25)
        bx, by = draw_lumen(
            img, em, cam, -220, GROUND,
            mood=mood, eye=eye, gaze_x=kf(t, [(18, -1), (25, 1), (31, 0)]),
            tilt=head_tilt + shake, bulb=bulb, squash=squash, dust=dust,
        )
        overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        if 35.7 < t < 48:
            peak = math.sin(math.pi * clamp((t - 35.7) / 12.3))
            draw_dust(overlay, t * 3.0, amount=3.4 * peak, seed=41, drift=4.0, count=210)
            img.paste(overlay, (0, 0), overlay)
        draw_dust(em, t, amount=.85 if t < 35 else 1.7, seed=3, drift=.35)
        lights = [(bx, by, 265, .84 * bulb, (1.0, .78, .47))]
        img = apply_lighting(img, em, cam, lights, ambient=.018, haze=.025, vignette=.48)
        return add_letterbox(img)

    # 0:52–1:45 — EXPLORATION. His bulb is a moving island in the dark.
    if t < 105:
        lx = kf(t, [(52, -210), (62, -80), (74, 70), (86, 150), (98, 208), (105, 226)])
        cam = Camera(x=kf(t, [(52, -140), (70, -20), (89, 100), (105, 185)]), y=278,
                     zoom=kf(t, [(52, 1.04), (105, 1.14)]))
        draw_station_room(img, cam, clean=0, awake=0)
        draw_floor_lamp(img, em, cam, LAMP_X, GROUND, on=0, tilt=0)
        draw_switch(img, cam, SWITCH_X, 300, on=False)
        gaze = math.sin((t - 52) * .42) * .9
        tilt = math.sin((t - 52) * .20) * 4
        if t > 92:
            gaze = -1.2
            tilt = -6
        bx, by = draw_lumen(img, em, cam, lx, GROUND, facing=1, gaze_x=gaze,
                            tilt=tilt, bulb=.82, wheel=(t - 52) * 3.3, dust=.02)
        draw_dust(em, t, amount=.9, seed=5, drift=.4)
        img = apply_lighting(img, em, cam, [(bx, by, 290, .90, (1.0, .78, .48))],
                             ambient=.017, vignette=.46)
        return add_letterbox(img)

    # 1:45–2:12 — ACCIDENT / FIRST LIGHT.
    if t < 132:
        cam = Camera(x=kf(t, [(105, 205), (113, 235), (132, 240)]), y=275,
                     zoom=kf(t, [(105, 1.18), (117, 1.34), (132, 1.19)]))
        draw_station_room(img, cam, clean=0, awake=0)
        tilt_lamp = kf(t, [(105, 0), (107, 14), (109.5, -10), (112, 6), (114.5, -3), (117, 0)])
        lamp_on = 0.0
        if 116.2 <= t < 117.1:
            lamp_on = .22 if int((t - 116.2) * 9) % 2 else 0
        elif 118.2 <= t < 119.5:
            lamp_on = .45 if int((t - 118.2) * 7) % 2 else .04
        elif t >= 120.5:
            lamp_on = q(t, 120.5, 123.0)
        draw_floor_lamp(img, em, cam, LAMP_X, GROUND, on=lamp_on, tilt=tilt_lamp)
        lx = kf(t, [(105, 226), (107.2, 236), (108, 206), (111, 190), (132, 186)])
        mood = "panic" if 106.7 < t < 111.5 else "neutral"
        gaze = 1.2 if t > 111 else 0
        bx, by = draw_lumen(img, em, cam, lx, GROUND, mood=mood, gaze_x=gaze,
                            tilt=kf(t, [(105, -5), (108, -15), (112, 8), (120, 0), (132, 3)]),
                            bulb=.82, wheel=(t - 105) * 3.0)
        lights = [(bx, by, 285, .84, (1.0, .78, .48))]
        if lamp_on:
            lights.append((LAMP_X, 247, 460, 1.05 * lamp_on, (1.0, .82, .55)))
        draw_dust(em, t, amount=1.1, seed=7, drift=.35)
        img = apply_lighting(img, em, cam, lights, ambient=.018 + .05 * lamp_on,
                             haze=.018, vignette=.42 - .08 * lamp_on)
        return add_letterbox(img)

    # 2:12–3:06 — Lumen deliberately wakes the room.
    if t < 186:
        lx = kf(t, [(132, 187), (141, 310), (150, 500), (163, 710), (178, 980), (186, 1080)])
        cam = Camera(x=kf(t, [(132, 245), (150, 420), (169, 690), (186, 820)]), y=277,
                     zoom=kf(t, [(132, 1.14), (155, .98), (186, .92)]))
        starts = [143.0, 149.5, 155.7, 161.0, 166.0, 170.6, 175.3, 180.0]
        levels = [q(t, s, s + 1.2) for s in starts]
        awake = sum(levels) / len(levels)
        draw_station_room(img, cam, clean=0, awake=awake)
        draw_floor_lamp(img, em, cam, LAMP_X, GROUND, on=1.0)
        draw_switch(img, cam, SWITCH_X, 300, on=t > 154.5,
                    highlight=max(0, 1 - abs(t - 152.5) / 2.6))
        for x, on in zip(LIGHT_XS, levels):
            stutter = on
            if 0 < on < .8:
                stutter *= .35 + .65 * (1 if int(t * 10 + x) % 3 else .15)
            draw_ceiling_light(img, em, cam, x, on=stutter)
        mood = "happy" if t > 158 else "neutral"
        bounce = math.sin(t * 5.5) * (1.2 if t > 160 else .4)
        bx, by = draw_lumen(img, em, cam, lx, GROUND + bounce, mood=mood,
                            gaze_x=.75, bulb=.72, wheel=(t - 132) * 4.2,
                            tilt=math.sin(t * 2.2) * 2.5)
        lights = [(bx, by, 255, .7, (1.0, .78, .48)), (LAMP_X, 247, 410, .96, (1.0, .82, .55))]
        for x, on in zip(LIGHT_XS, levels):
            lights.append((x, 125, 335, .58 * on, (.86, .94, 1.0)))
        draw_dust(em, t, amount=.85, seed=11, drift=.5)
        img = apply_lighting(img, em, cam, lights, ambient=.03 + .18 * awake,
                             haze=.014, vignette=.38 - .16 * awake)
        return add_letterbox(img)

    # 3:06–4:12 — MOTH: curiosity -> synchronized panic -> trust.
    if t < 252:
        cam = Camera(x=kf(t, [(186, 830), (205, 965), (224, 875), (239, 820), (252, 850)]), y=276,
                     zoom=kf(t, [(186, .94), (205, 1.10), (224, .98), (239, 1.22), (252, 1.14)]))
        draw_station_room(img, cam, clean=0, awake=1.0)
        draw_floor_lamp(img, em, cam, LAMP_X, GROUND, on=1)
        for x in LIGHT_XS:
            draw_ceiling_light(img, em, cam, x, on=1)
        if t < 207:
            lx = 1055
        elif t < 229:
            p = (t - 207) / 22
            lx = 1000 + math.sin(p * math.pi * 7.0) * 170
        else:
            lx = kf(t, [(229, 940), (235, 900), (252, 905)])
        if t < 198:
            mx = kf(t, [(186, 1380), (191, 1240), (198, 1095)])
            my = kf(t, [(186, 165), (191, 130), (198, 285)]) + math.sin(t * 6) * 13
            perch = False
            panic = 0
        elif t < 207:
            mx = lx + 38
            my = 318
            perch = True
            panic = 0
        elif t < 229:
            p = (t - 207) / 22
            mx = lx + math.cos(p * math.pi * 10) * (80 + 55 * math.sin(p * math.pi))
            my = 285 + math.sin(p * math.pi * 14) * 68
            perch = False
            panic = .95
        elif t < 241:
            mx = 1005
            my = 275
            perch = False
            panic = 0
        else:
            land = q(t, 241, 248.5)
            mx = 1005 + (lx + 37 - 1005) * land
            my = 275 + (318 - 275) * land + math.sin(t * 4) * (1 - land) * 5
            perch = land > .92
            panic = 0

        mood = "neutral"
        tilt = 0
        gaze = .4
        if 200 < t < 207:
            gaze = 1.25
            tilt = kf(t, [(200, 0), (207, 9)])
        elif 207 <= t < 229:
            mood = "panic"
            tilt = math.sin(t * 9) * 11
            gaze = math.sin(t * 12)
        elif 229 <= t < 238:
            mood = "neutral"
            gaze = 1.2
        elif t >= 238:
            mood = "happy"
            gaze = .75
        bx, by = draw_lumen(img, em, cam, lx, GROUND, mood=mood, gaze_x=gaze,
                            tilt=tilt, bulb=.72, wheel=(t - 186) * (7 if mood == "panic" else 1.0))
        draw_moth(img, em, cam, mx, my, t, panic=panic, perch=perch, glow=.72)
        lights = [(bx, by, 250, .65, (1.0, .78, .48))]
        for x in LIGHT_XS:
            lights.append((x, 125, 325, .57, (.86, .94, 1.0)))
        lights.append((mx, my, 110, .20, (.70, .86, 1.0)))
        draw_dust(em, t, amount=.72, seed=14, drift=.5)
        img = apply_lighting(img, em, cam, lights, ambient=.21, vignette=.22)
        return add_letterbox(img)

    # 4:12–5:35 — TOGETHER: restore the first chamber.
    if t < 335:
        clean = qq(t, 252, 328)
        lx = kf(t, [(252, 900), (263, 720), (276, 470), (291, 810), (305, 1200), (319, 1460), (335, 1160)])
        cam = Camera(x=kf(t, [(252, 840), (270, 650), (292, 820), (315, 1180), (335, 1020)]), y=276,
                     zoom=kf(t, [(252, 1.10), (272, .91), (306, .86), (335, .82)]))
        draw_station_room(img, cam, clean=clean, awake=1.0)
        draw_floor_lamp(img, em, cam, LAMP_X, GROUND, on=1)
        for x in LIGHT_XS:
            draw_ceiling_light(img, em, cam, x, on=1)

        perch_windows = [(252, 257), (283, 288), (327, 335)]
        perched = any(a <= t <= b for a, b in perch_windows)
        if perched:
            mx, my = lx + 38, 318
        else:
            mx = lx + 120 + math.sin(t * .8) * 70
            my = 245 + math.sin(t * 2.2) * 45
        arm = (1, -55, 42) if 307 <= t <= 314 else None
        bx, by = draw_lumen(img, em, cam, lx, GROUND, mood="happy", gaze_x=.55,
                            bulb=.66, wheel=(t - 252) * 3.2,
                            tilt=math.sin(t * 1.7) * 2, arm=arm)
        draw_moth(img, em, cam, mx, my, t, perch=perched, glow=.68)

        d = ImageDraw.Draw(img)
        px0, py0 = cam.p(1510, 384)
        px1, py1 = cam.p(1590, 430)
        d.rectangle([px0, py0, px1, py1], fill=(71, 74, 69), outline=(36, 41, 38))
        plant = q(t, 312, 324)
        if plant > 0:
            sx, sy = cam.p(1550, 384)
            stem = cam.scale(36 * plant)
            d.line([(sx, sy), (sx, sy - stem)], fill=(83, 145, 91), width=max(1, int(cam.scale(3))))
            if plant > .35:
                for side, off in [(-1, .52), (1, .68), (-1, .83)]:
                    yy = sy - stem * off
                    ww = cam.scale(13 * plant)
                    hh = cam.scale(6 * plant)
                    d.ellipse([sx + side * ww * .2 - ww, yy - hh, sx + side * ww * .2 + ww, yy + hh],
                              fill=(74, 132, 82))

        lights = [(bx, by, 245, .58, (1.0, .78, .48)), (mx, my, 95, .16, (.72, .88, 1.0))]
        for x in LIGHT_XS:
            lights.append((x, 125, 335, .62, (.88, .96, 1.0)))
        lights.append((LAMP_X, 247, 390, .78, (1.0, .83, .58)))
        draw_dust(em, t, amount=max(.10, .70 * (1 - clean)), seed=18, drift=.55)
        img = apply_lighting(img, em, cam, lights, ambient=.21 + .12 * clean,
                             haze=.010 * (1 - clean), vignette=.22 - .08 * clean)
        return add_letterbox(img)

    # 5:35–5:57 — THEY THINK THEY'RE DONE.
    if t < 357:
        cam = Camera(x=760, y=276, zoom=kf(t, [(335, .79), (349, .72), (357, .74)]))
        draw_station_room(img, cam, clean=1, awake=1, reveal=False)
        draw_floor_lamp(img, em, cam, LAMP_X, GROUND, on=1)
        for x in LIGHT_XS:
            draw_ceiling_light(img, em, cam, x, on=1)
        lx = 850
        bx, by = draw_lumen(img, em, cam, lx, GROUND, mood="happy", gaze_x=.1,
                            tilt=math.sin((t - 335) * .65) * 1.6, bulb=.64, wheel=0)
        if t < 347:
            a = (t - 335) * .72
            mx = lx + math.cos(a) * 85
            my = 280 + math.sin(a * 1.3) * 55
            perch = False
        else:
            land = q(t, 347, 351)
            mx = (lx + 85) * (1 - land) + (lx + 38) * land
            my = 280 * (1 - land) + 318 * land
            perch = land > .9
        draw_moth(img, em, cam, mx, my, t, perch=perch, glow=.7)
        lights = [(bx, by, 230, .55, (1.0, .78, .48)), (mx, my, 90, .17, (.72, .88, 1.0))]
        for x in LIGHT_XS:
            lights.append((x, 125, 340, .62, (.90, .97, 1.0)))
        img = apply_lighting(img, em, cam, lights, ambient=.34, vignette=.12)
        return add_letterbox(img)

    # 5:57–6:11 — THE REST OF THE STATION.
    if t < 371:
        if t < 361:
            cam = Camera(x=1120, y=278, zoom=.76)
            draw_station_room(img, cam, clean=1, awake=1, reveal=True)
            draw_floor_lamp(img, em, cam, LAMP_X, GROUND, on=1)
            for x in LIGHT_XS:
                draw_ceiling_light(img, em, cam, x, on=1)
            open_u = qq(t, 357, 361)
            d = ImageDraw.Draw(img)
            x0, y0 = cam.p(1790, 145)
            x1, y1 = cam.p(1880, 430)
            mid = (x0 + x1) / 2
            half = abs(x1 - x0) * .5 * open_u
            d.rectangle([mid - half, y0, mid + half, y1], fill=(3, 5, 10))
            bx, by = draw_lumen(img, em, cam, 1490, GROUND, mood="neutral", gaze_x=1.25,
                                tilt=kf(t, [(357, 0), (361, 8)]), bulb=.62)
            mx, my = 1528, 318
            draw_moth(img, em, cam, mx, my, t, perch=True, glow=.65)
            lights = [(bx, by, 225, .55, (1.0, .78, .48))]
            for x in LIGHT_XS:
                lights.append((x, 125, 340, .60, (.90, .97, 1.0)))
            img = apply_lighting(img, em, cam, lights, ambient=.31, vignette=.14)
            return add_letterbox(img)

        cam = Camera(x=kf(t, [(361, 1900), (365, 2310), (369.5, 2580), (371, 2580)]),
                     y=kf(t, [(361, 284), (369.5, 285)]),
                     zoom=kf(t, [(361, .82), (365, .55), (369.5, .39), (371, .39)]))
        draw_far_station(img, cam, power=.11)
        em = make_emissive()
        d = ImageDraw.Draw(img)
        ax0, ay0 = cam.p(1665, 270)
        ax1, ay1 = cam.p(1860, 435)
        d.rectangle([ax0, ay0, ax1, ay1], fill=(55, 61, 66))
        bx, by = draw_lumen(img, em, cam, 1780, 430, mood="neutral", gaze_x=1,
                            tilt=-2, bulb=.68)
        mx, my = 1818, 318
        draw_moth(img, em, cam, mx, my, t, perch=True, glow=.62)
        img = apply_lighting(img, em, cam,
                             [(1780, 315, 290, .72, (1.0, .78, .48)),
                              (1760, 320, 420, .24, (.92, .94, .88))],
                             ambient=.055, haze=.012, vignette=.36)
        return add_letterbox(img)

    return title_card(t)


def frames():
    n = int(DURATION * FPS)
    for i in range(n):
        yield frame_at(i / FPS)


def render_stills(times: list[float]):
    out = ROOT / "stills"
    out.mkdir(parents=True, exist_ok=True)
    for t in times:
        path = out / f"ep01_{t:06.1f}.png"
        frame_at(t).save(path)
        print(path)


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("usage: ep01_first_light.py stills <seconds...> | render <output.mp4>")
        return 2
    mode = argv[1]
    if mode == "stills":
        times = [float(x) for x in argv[2:]] or [8, 40, 98, 122, 169, 202, 218, 246, 282, 327, 349, 366]
        render_stills(times)
        return 0
    if mode == "render":
        out = argv[2] if len(argv) > 2 else str(ROOT / "media" / "ep01_silent.mp4")
        Path(out).parent.mkdir(parents=True, exist_ok=True)
        encode(frames(), out, fps=FPS, crf=19, preset="medium")
        print(out)
        return 0
    raise SystemExit(f"unknown mode: {mode}")


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
