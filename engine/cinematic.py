"""Shared renderer helpers for the cinematic LUMEN remake."""
from __future__ import annotations
import math, os, subprocess
from dataclasses import dataclass
from functools import lru_cache
from typing import Iterable, Sequence

import imageio_ffmpeg
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 960, 540
FPS = int(os.environ.get("LUMEN_FPS", "24"))
S = max(1, int(os.environ.get("LUMEN_SCALE", "1")))
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def clamp(v, lo=0.0, hi=1.0):
    return max(lo, min(hi, v))


def smooth(u):
    u = clamp(u)
    return u * u * (3.0 - 2.0 * u)


def smoother(u):
    u = clamp(u)
    return u*u*u*(u*(u*6-15)+10)


def eout(u):
    u = clamp(u)
    return 1.0 - (1.0-u)**3


def kf(t, pts, easing=smooth):
    if t <= pts[0][0]:
        return pts[0][1]
    for (t0, v0), (t1, v1) in zip(pts, pts[1:]):
        if t <= t1:
            q = easing((t-t0)/(t1-t0))
            return v0 + (v1-v0)*q
    return pts[-1][1]


def lerp(a, b, u):
    return a + (b-a)*u


def font(sz):
    return ImageFont.truetype(FONT, int(sz*S))


@dataclass
class Camera:
    x: float
    y: float = H/2
    zoom: float = 1.0

    def p(self, wx: float, wy: float):
        return ((wx-self.x)*self.zoom + W/2)*S, ((wy-self.y)*self.zoom + H/2)*S

    def scale(self, v: float):
        return v*self.zoom*S


def _rect_world(cam: Camera, box):
    x0,y0 = cam.p(box[0], box[1]); x1,y1 = cam.p(box[2], box[3]);
    return [x0,y0,x1,y1]


def make_canvas(rgb=(8,10,15)):
    return Image.new("RGB", (W*S, H*S), rgb)


def make_emissive():
    return Image.new("RGBA", (W*S, H*S), (0,0,0,0))


# ---------- station ----------
def draw_station_room(img: Image.Image, cam: Camera, room_left=-700, room_right=1900,
                      clean=0.0, awake=0.0, reveal=False):
    """Draw the first maintenance chamber. clean=0 dusty, 1 restored."""
    d = ImageDraw.Draw(img)
    wall = (32,39,52); floor=(38,39,48)
    d.rectangle(_rect_world(cam, (room_left, 0, room_right, 430)), fill=wall)
    d.rectangle(_rect_world(cam, (room_left, 430, room_right, 610)), fill=floor)
    for y in range(0, 430, 18):
        k = y/430
        c = (int(24+21*k), int(30+22*k), int(42+28*k))
        d.rectangle(_rect_world(cam, (room_left, y, room_right, y+20)), fill=c)
    for yy, th in ((48,18),(82,9)):
        d.rectangle(_rect_world(cam,(room_left,yy,room_right,yy+th)),fill=(74,79,89))
        d.rectangle(_rect_world(cam,(room_left,yy+3,room_right,yy+5)),fill=(118,125,137))
    for x in range(int(room_left)+70, int(room_right), 235):
        d.rectangle(_rect_world(cam,(x,40,x+12,107)),fill=(51,55,65))
    for x in range(int(room_left), int(room_right), 210):
        d.rectangle(_rect_world(cam,(x,130,x+4,430)),fill=(22,28,38))
        for k in range(4):
            px,py=cam.p(x+16,165+k*60); r=cam.scale(3.2)
            d.ellipse([px-r,py-r,px+r,py+r],fill=(72,81,95))
    d.rectangle(_rect_world(cam,(room_left,419,room_right,426)),fill=(75,78,88))
    for x in range(int(room_left)-100, int(room_right)+100, 70):
        x0,y0=cam.p(x,438); x1,y1=cam.p(x-42,600)
        d.line([(x0,y0),(x1,y1)], fill=(28,29,36), width=max(1,int(cam.scale(1.4))))
    for y in (470,520,575):
        x0,y0=cam.p(room_left,y); x1,y1=cam.p(room_right,y)
        d.line([(x0,y0),(x1,y1)],fill=(30,31,39),width=max(1,int(cam.scale(1))))
    for x in (-410, 1465):
        d.rounded_rectangle(_rect_world(cam,(x,165,x+178,430)),radius=int(cam.scale(7)),fill=(59,66,78),outline=(15,18,25),width=max(1,int(cam.scale(3))))
        mx,_=cam.p(x+89,0); _,y0=cam.p(0,165); _,y1=cam.p(0,430)
        d.line([(mx,y0),(mx,y1)],fill=(19,23,31),width=max(1,int(cam.scale(3))))
        for k in range(5):
            xx=x+12+k*31
            pts=[cam.p(xx,186),cam.p(xx+18,186),cam.p(xx+3,206),cam.p(xx-15,206)]
            d.polygon(pts,fill=(164,126,38))
    d.rounded_rectangle(_rect_world(cam,(770,155,1120,335)),radius=int(cam.scale(5)),fill=(4,6,14),outline=(85,92,108),width=max(1,int(cam.scale(6))))
    rr=np.random.RandomState(13)
    for _ in range(62):
        sx=790+rr.rand()*310; sy=170+rr.rand()*145
        px,py=cam.p(sx,sy); r=cam.scale(0.7+rr.rand()*1.0)
        d.ellipse([px-r,py-r,px+r,py+r],fill=(190,205,230))
    for bx in (110, 300, 500):
        d.rounded_rectangle(_rect_world(cam,(bx,178,bx+116,248)),radius=int(cam.scale(5)),fill=(13,16,22),outline=(68,76,90),width=max(1,int(cam.scale(3))))
        if awake>0.06:
            col=(45, min(255,125+int(90*awake)), min(255,160+int(80*awake)))
            d.rectangle(_rect_world(cam,(bx+11,189,bx+105,235)),fill=tuple(int(c*awake) for c in col))
            for q in range(4):
                y=195+q*9
                d.line([cam.p(bx+18,y),cam.p(bx+50+q*9,y)],fill=(110,235,245),width=max(1,int(cam.scale(1))))
    d.rectangle(_rect_world(cam,(1200,350,1390,365)),fill=(75,76,81))
    for lx in (1214,1362): d.rectangle(_rect_world(cam,(lx,365,lx+10,430)),fill=(57,59,65))
    crates=[(-80,388,54,42),(420,400,62,30),(1260,388,55,35),(1330,401,43,27)]
    for i,(x,y,w,h) in enumerate(crates):
        dx=(i%2)*clean*68; dy=-clean*(10+(i%3)*3)
        box=_rect_world(cam,(x+dx,y+dy,x+w+dx,y+h+dy))
        d.rectangle(box,fill=(108,80,49),outline=(53,38,26),width=max(1,int(cam.scale(2))))
        d.line([cam.p(x+dx,y+dy),cam.p(x+w+dx,y+h+dy)],fill=(75,52,32),width=max(1,int(cam.scale(2))))
    if clean<0.98:
        alpha=1-clean
        for i,(x,y) in enumerate(((210,443),(650,455),(1010,448),(1570,450))):
            pts=[cam.p(x+q*23, y+math.sin(q*1.9+i)*9) for q in range(6)]
            col=tuple(int(v*alpha) for v in (72,64,63))
            d.line(pts,fill=col,width=max(1,int(cam.scale(3))))
    if clean>0.55:
        c=clamp((clean-0.55)/0.45)
        for x in range(-550,1750,115):
            px,py=cam.p(x,425); r=cam.scale(3.2)
            d.ellipse([px-r,py-r,px+r,py+r],fill=(int(70*c),int(220*c),int(230*c)))
    if reveal:
        d.rounded_rectangle(_rect_world(cam,(1790,145,1880,430)),radius=int(cam.scale(4)),fill=(7,9,15),outline=(76,82,95),width=max(1,int(cam.scale(4))))


def draw_far_station(img: Image.Image, cam: Camera, power=0.12):
    """Huge multi-level station view used for the final reveal."""
    d=ImageDraw.Draw(img)
    d.rectangle([0,0,W*S,H*S],fill=(4,6,11))
    for i in range(11):
        inset=i*52
        x0,y0=cam.p(1680+inset,65+inset*0.18)
        x1,y1=cam.p(3480-inset,510-inset*0.08)
        shade=35+i*2
        d.rounded_rectangle([x0,y0,x1,y1],radius=max(1,int(cam.scale(8))),outline=(shade,shade+5,shade+14),width=max(1,int(cam.scale(9))))
    for level in (155,250,346,435):
        d.rectangle(_rect_world(cam,(1740,level,3420,level+12)),fill=(39,44,54))
        for x in range(1790,3380,150):
            d.rectangle(_rect_world(cam,(x,level-18,x+7,level+12)),fill=(29,34,43))
            if (x//150 + int(level))%3==0:
                px,py=cam.p(x+18,level-8); r=cam.scale(2.8)
                col=(int(30*power),int(150*power),int(170*power))
                d.ellipse([px-r,py-r,px+r,py+r],fill=col)
    for x in (1900,2240,2650,3060,3320):
        d.rectangle(_rect_world(cam,(x,110,x+24,470)),fill=(25,29,38))
    for x in (2030,2870):
        d.rounded_rectangle(_rect_world(cam,(x,310,x+190,470)),radius=int(cam.scale(8)),fill=(12,15,22),outline=(52,58,70),width=max(1,int(cam.scale(4))))
    for row,y in enumerate((120,205,298,392)):
        for col,x in enumerate(range(1810,3370,120)):
            on=((row*13+col*7)%17==0)
            p=power*(1.0 if on else 0.05)
            px,py=cam.p(x,y); r=cam.scale(2.4)
            d.ellipse([px-r,py-r,px+r,py+r],fill=(int(200*p),int(225*p),int(230*p)))
    haze=Image.new("RGBA",img.size,(0,0,0,0)); hd=ImageDraw.Draw(haze)
    for i in range(7):
        y=int((90+i*64)*S); hd.rectangle([0,y,W*S,y+int(26*S)],fill=(95,105,125,10+i*2))
    haze=haze.filter(ImageFilter.GaussianBlur(max(1,18*S)))
    img.paste(haze,(0,0),haze)


def draw_floor_lamp(img, emissive, cam, x, y=430, on=0.0, tilt=0.0):
    d=ImageDraw.Draw(img); e=ImageDraw.Draw(emissive)
    layer=Image.new("RGBA",(120*S,270*S),(0,0,0,0)); ld=ImageDraw.Draw(layer)
    ld.ellipse([38*S,246*S,82*S,258*S],fill=(58,62,72),outline=(24,27,34))
    ld.rectangle([57*S,58*S,63*S,250*S],fill=(93,99,110))
    ld.polygon([(28*S,68*S),(92*S,68*S),(76*S,35*S),(44*S,35*S)],fill=(82,89,102),outline=(35,39,47))
    ld.ellipse([45*S,61*S,75*S,79*S],fill=(145,126,84))
    if abs(tilt)>0.05: layer=layer.rotate(tilt,resample=Image.BICUBIC,center=(60*S,250*S),expand=False)
    ox,oy=cam.p(x-60/cam.zoom,y-250/cam.zoom)
    if abs(cam.zoom-1)>1e-3:
        layer=layer.resize((int(layer.width*cam.zoom),int(layer.height*cam.zoom)),Image.BICUBIC)
        ox,oy=cam.p(x-60,y-250)
    img.paste(layer,(int(ox),int(oy)),layer)
    if on>0.001:
        px,py=cam.p(x,y-183)
        rr=cam.scale(16)
        e.ellipse([px-rr,py-rr*0.45,px+rr,py+rr*0.45],fill=(255,231,164,int(255*clamp(on))))


def draw_ceiling_light(img, emissive, cam, x, y=126, on=0.0):
    d=ImageDraw.Draw(img); e=ImageDraw.Draw(emissive)
    d.rounded_rectangle(_rect_world(cam,(x-45,y-10,x+45,y+10)),radius=max(1,int(cam.scale(4))),fill=(72,78,90),outline=(34,38,46),width=max(1,int(cam.scale(2))))
    if on>0.001:
        d.rounded_rectangle(_rect_world(cam,(x-36,y-4,x+36,y+4)),radius=max(1,int(cam.scale(2))),fill=(180,177,152))
        e.rounded_rectangle(_rect_world(cam,(x-37,y-5,x+37,y+5)),radius=max(1,int(cam.scale(2))),fill=(255,239,190,int(240*on)))


def draw_switch(img, cam, x, y, on=False, highlight=0.0):
    d=ImageDraw.Draw(img)
    d.rounded_rectangle(_rect_world(cam,(x-15,y-23,x+15,y+23)),radius=max(1,int(cam.scale(4))),fill=(46,52,64),outline=(86,94,109),width=max(1,int(cam.scale(2))))
    yy=y+(-8 if on else 7)
    d.rounded_rectangle(_rect_world(cam,(x-8,yy-8,x+8,yy+8)),radius=max(1,int(cam.scale(3))),fill=(122,128,138))
    if highlight>0:
        px,py=cam.p(x,y); rr=cam.scale(28+8*highlight)
        d.ellipse([px-rr,py-rr,px+rr,py+rr],outline=(int(80*highlight),int(220*highlight),int(245*highlight)),width=max(1,int(cam.scale(2))))


def draw_lumen(img, emissive, cam, x, y=430, *, facing=1, mood="neutral", eye=1.0,
               gaze_x=0.0, gaze_y=0.0, tilt=0.0, wheel=0.0, bulb=0.0,
               squash=1.0, dust=0.0, arm=None):
    """Draw Lumen at wheel contact (x,y). facing +/-1."""
    K=cam.zoom
    size=250
    L=Image.new("RGBA",(size*S,size*S),(0,0,0,0)); E=Image.new("RGBA",(size*S,size*S),(0,0,0,0))
    d=ImageDraw.Draw(L); e=ImageDraw.Draw(E)
    def R(a,b,c,d_): return [a*S,b*S,c*S,d_*S]
    d.ellipse(R(101,188,149,236),fill=(28,32,40),outline=(10,12,17),width=max(1,2*S))
    for k in range(4):
        a=wheel+k*math.pi/2
        d.line([(125*S,212*S),((125+18*math.cos(a))*S,(212+18*math.sin(a))*S)],fill=(116,125,139),width=max(1,3*S))
    d.ellipse(R(118,205,132,219),fill=(150,158,171))
    by=199-58*squash
    d.rounded_rectangle(R(90,by,160,200),radius=14*S,fill=(65,145,164),outline=(18,47,57),width=max(1,2*S))
    d.rounded_rectangle(R(101,by+14,149,by+22),radius=3*S,fill=(44,110,130))
    d.ellipse(R(148,by+27,159,by+38),fill=(24,29,37),outline=(190,190,120),width=max(1,2*S))
    if arm:
        side, ang, reach = arm
        ax=90 if side<0 else 160; ay=by+32
        th=math.radians(ang)
        ex=ax+math.cos(th)*reach*(1 if side>0 else -1); ey=ay+math.sin(th)*reach
        d.line([(ax*S,ay*S),(ex*S,ey*S)],fill=(90,100,112),width=max(1,4*S))
        d.ellipse(R(ex-4,ey-4,ex+4,ey+4),fill=(135,145,158))
    hx,hy=125+tilt*0.35,by-25
    d.line([(hx*S,(hy-28)*S),(hx*S,(hy-44)*S)],fill=(145,153,165),width=max(1,3*S))
    d.ellipse(R(hx-38,hy-34,hx+38,hy+34),fill=(208,216,224),outline=(65,72,84),width=max(1,3*S))
    d.rounded_rectangle(R(hx-27,hy-14,hx+27,hy+13),radius=10*S,fill=(13,18,28))
    gx=gaze_x*4; gy=gaze_y*3
    for ex in (hx-11,hx+11):
        ex += gx
        if eye <= .02: continue
        if mood=="happy":
            e.arc(R(ex-7,hy-5+gy,ex+7,hy+9+gy),200,340,fill=(126,244,255,255),width=max(1,3*S))
        elif mood=="panic":
            e.ellipse(R(ex-6,hy-8+gy,ex+6,hy+8+gy),fill=(155,250,255,255))
            d.ellipse(R(ex-2,hy-3+gy,ex+2,hy+3+gy),fill=(8,14,22))
        elif mood=="tired":
            e.ellipse(R(ex-5,hy-1+gy,ex+5,hy+6+gy),fill=(105,190,225,220))
        else:
            e.ellipse(R(ex-5,hy-6*eye+gy,ex+5,hy+6*eye+gy),fill=(126,244,255,255))
    bx,byb=hx,hy-50
    d.ellipse(R(bx-9,byb-9,bx+9,byb+9),fill=(125,110,80),outline=(70,62,47))
    if bulb>0:
        e.ellipse(R(bx-9,byb-9,bx+9,byb+9),fill=(255,228,153,int(255*clamp(bulb))))
    if dust>0.01:
        rr=np.random.RandomState(9)
        for _ in range(26):
            px=rr.uniform(88,162); py=rr.uniform(55,205)
            rad=rr.uniform(1.0,2.8)
            d.ellipse(R(px-rad,py-rad,px+rad,py+rad),fill=(95,91,85,int(150*dust)))
    if facing<0:
        L=L.transpose(Image.FLIP_LEFT_RIGHT); E=E.transpose(Image.FLIP_LEFT_RIGHT)
    if abs(tilt)>0.08:
        L=L.rotate(tilt,resample=Image.BICUBIC,center=(125*S,212*S))
        E=E.rotate(tilt,resample=Image.BICUBIC,center=(125*S,212*S))
    if abs(K-1)>1e-3:
        nw,nh=int(size*S*K),int(size*S*K)
        L=L.resize((nw,nh),Image.LANCZOS); E=E.resize((nw,nh),Image.LANCZOS)
    ox,oy=cam.p(x-125,y-212)
    img.paste(L,(int(ox),int(oy)),L); emissive.paste(E,(int(ox),int(oy)),E)
    return x, y-(212-(hy-50))*1.0


def draw_moth(img, emissive, cam, x, y, t, *, panic=0.0, perch=False, glow=0.6, facing=1):
    d=ImageDraw.Draw(img); e=ImageDraw.Draw(emissive)
    sx,sy=cam.p(x,y)
    sc=cam.scale(1.0)
    hz=18+panic*18
    flap=math.sin(2*math.pi*hz*t)
    wingw=(13+5*panic)*sc; wingh=(7+3*panic)*sc
    body=(68,79,102)
    if perch: flap=-0.15; wingh*=0.72
    alpha=int(78+72*glow)
    for side in (-1,1):
        rootx=sx+side*2*sc; rooty=sy-2*sc
        tipx=sx+side*(wingw+5*sc+flap*1.5*sc)
        tipy=sy-(2+flap*2)*sc
        pts=[(rootx,rooty-wingh*.55),(tipx,tipy-wingh),(tipx+side*3*sc,tipy+wingh*.18),(rootx,rooty+wingh*.7)]
        e.polygon(pts,fill=(180,220,255,alpha))
        d.line([(rootx,rooty),(tipx,tipy)],fill=(102,126,151),width=max(1,int(sc)))
    d.ellipse([sx-3*sc,sy-6*sc,sx+3*sc,sy+7*sc],fill=body)
    d.ellipse([sx-3*sc,sy-11*sc,sx+3*sc,sy-5*sc],fill=(84,98,124))
    for side in (-1,1):
        d.line([(sx+side*1*sc,sy-9*sc),(sx+side*7*sc,sy-17*sc)],fill=(115,130,155),width=max(1,int(1.2*sc)))
    e.ellipse([sx-2.5*sc,sy-2*sc,sx+2.5*sc,sy+5*sc],fill=(225,244,255,int(120+120*glow)))


@lru_cache(maxsize=32)
def _dust_seed(seed, count):
    rr=np.random.RandomState(seed)
    return [(rr.rand(),rr.rand(),rr.uniform(.35,1.8),rr.uniform(.15,.75),rr.uniform(-1,1)) for _ in range(count)]


def draw_dust(emissive_or_overlay: Image.Image, t, amount=1.0, seed=1, drift=1.0, count=95):
    if amount<=0.002: return
    d=ImageDraw.Draw(emissive_or_overlay)
    for i,(rx,ry,r,b,dx) in enumerate(_dust_seed(seed,count)):
        x=((rx*W + t*(3+7*b)*drift + i*17)% (W+60))-30
        y=((ry*H + math.sin(t*.18+i)*12 + t*(.4+b*.7))%(H+40))-20
        rr=max(1,r*S)
        a=int(42*amount*b)
        d.ellipse([x*S-rr,y*S-rr,x*S+rr,y*S+rr],fill=(205,195,175,a))


def apply_lighting(img: Image.Image, emissive: Image.Image, cam: Camera, lights: Sequence,
                   ambient=0.08, haze=0.0, vignette=0.20):
    """lights: iterable of (world_x, world_y, radius, intensity, tint RGB[0..1])"""
    lw,lh=max(80,W//4),max(45,H//4)
    ys,xs=np.mgrid[0:lh,0:lw]
    sx=xs*(W/lw); sy=ys*(H/lh)
    wx=(sx-W/2)/cam.zoom + cam.x
    wy=(sy-H/2)/cam.zoom + cam.y
    out=np.full((lh,lw,3),ambient,np.float32)
    for lx,ly,r,k,tint in lights:
        if r<=1 or k<=0: continue
        dd=np.sqrt((wx-lx)**2 + ((wy-ly)*1.08)**2)/r
        f=np.clip(1-dd,0,1)**1.65*k
        for c in range(3): out[...,c]+=f*tint[c]
    out=np.clip(out,0,1.35)
    lm=Image.fromarray((out*255/1.35).astype(np.uint8)).resize((W*S,H*S),Image.BILINEAR)
    lm=np.asarray(lm).astype(np.float32)*1.35/255
    arr=np.asarray(img).astype(np.float32)*lm
    ea=np.asarray(emissive).astype(np.float32)
    a=ea[...,3:4]/255.0
    arr=arr*(1-a)+ea[...,:3]*a
    if np.max(ea[...,3])>0:
        glow=np.asarray(emissive.filter(ImageFilter.GaussianBlur(max(1,10*S)))).astype(np.float32)
        arr += glow[...,:3]*(glow[...,3:4]/255.0)*0.85
    if vignette>0:
        yy,xx=np.mgrid[0:H*S,0:W*S]
        nx=(xx-W*S/2)/(W*S/2); ny=(yy-H*S/2)/(H*S/2)
        vg=1-vignette*np.clip((nx*nx+ny*ny)*.72,0,1)
        arr*=vg[...,None]
    if haze>0:
        arr=arr*(1-haze)+np.array([68,75,88],dtype=np.float32)*haze
    return Image.fromarray(np.clip(arr,0,255).astype(np.uint8))


def add_letterbox(img, amount=1.0):
    if amount<=0: return img
    d=ImageDraw.Draw(img)
    h=int(28*S*amount)
    d.rectangle([0,0,W*S,h],fill=(0,0,0))
    d.rectangle([0,H*S-h,W*S,H*S],fill=(0,0,0))
    return img


def encode(frames: Iterable[Image.Image], out_path: str, fps=FPS, crf=19, preset="medium"):
    exe=imageio_ffmpeg.get_ffmpeg_exe()
    cmd=[exe,"-y","-f","rawvideo","-pix_fmt","rgb24","-s",f"{W}x{H}","-r",str(fps),"-i","-","-c:v","libx264","-pix_fmt","yuv420p","-crf",str(crf),"-preset",preset,"-movflags","+faststart",out_path]
    p=subprocess.Popen(cmd,stdin=subprocess.PIPE,stderr=subprocess.DEVNULL)
    try:
        for fr in frames:
            if fr.size!=(W,H): fr=fr.resize((W,H),Image.LANCZOS)
            p.stdin.write(np.asarray(fr.convert("RGB")).tobytes())
    finally:
        if p.stdin: p.stdin.close()
        p.wait()
    if p.returncode!=0: raise RuntimeError(f"ffmpeg failed with status {p.returncode}")
