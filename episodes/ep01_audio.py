"""Procedural soundtrack for LUMEN Episode 1: First Light."""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'engine'))
from audio import *

D=378.0


def wheel(dur,seed=1,energy=.5):
    base=noise(dur,.22,seed,.055)
    t=np.arange(len(base),dtype=np.float32)/SR
    motor=np.sin(2*np.pi*(78+7*np.sin(t*2*np.pi*.63))*t).astype(np.float32)*.13
    pulse=.42+.58*(np.sin(2*np.pi*(4.8+energy)*t)**2)
    return ((base*.56+motor)*pulse*.11*energy).astype(np.float32)


def flutter(dur,panic=0.0,seed=70):
    t=np.arange(int(dur*SR),dtype=np.float32)/SR
    hz=23+panic*21
    carrier=np.sin(2*np.pi*(1120+panic*360)*t)
    gate=(.5+.5*np.sin(2*np.pi*hz*t))**4
    airy=noise(dur,.22,seed,.11)
    return ((carrier*.34+airy*.66)*gate*env(len(t),.04,.08)*.11).astype(np.float32)


def chirp(f=1900,up=True,amp=.11):
    return glide(f,f*(1.27 if up else .76),.09,amp,.003,.035)


def hum(dur,amp=.05,f=58):
    t=np.arange(int(dur*SR),dtype=np.float32)/SR
    s=np.sin(2*np.pi*f*t)+.18*np.sin(2*np.pi*(f*2.01)*t)
    return (s.astype(np.float32)*env(len(t),1.5,2.0)*amp)


def build():
    tr=Track(D)
    tr.add(0,noise(D,.043,2,.0025))
    tr.add(0,hum(D,.022,42))
    tr.add(0,pad([midi(34),midi(41)],54,.075,6,8))
    for i,t0 in enumerate((4.2,9.8,17.1,25.7,33.5,47.4)):
        tr.add(t0,tone(145+17*(i%3),.045,.065,.001,.025,(1,.25)))
    for i,t0 in enumerate((5.8,9.3,12.8,14.0,16.9)):
        tr.add(t0,tone(510+i*48,.055,.10,.002,.03,(1,.2)))
        tr.add(t0+.06,glide(175+i*12,255+i*16,.11,.06))
    tr.add(17.6,bell(midi(76),1.8,.09))
    tr.add(20,pad([midi(45),midi(52)],34,.09,3,6))
    for k in range(13):
        tt=36.2+k*.57
        tr.add(tt,tone(96+(k%3)*18,.055,.095,.001,.03,(1,.28)))
        tr.add(tt+.025,noise(.14,.085,100+k,.18))
    for k in range(5): tr.add(37.0+k*1.35,glide(410,300,.16,.05))

    tr.add(52,wheel(53,4,.65))
    tr.add(52,pad([midi(40),midi(47)],53,.055,4,7))
    for k,n in enumerate((64,67,71,67,64,62)):
        tr.add(56+k*7.6,bell(midi(n),2.8,.05))

    tr.add(106.6,tone(61,.45,.42,.001,.32,(1,.4,.14)))
    tr.add(106.62,noise(.30,.30,201,.25))
    tr.add(106.68,bell(midi(50),2.5,.20))
    tr.add(108.1,glide(610,320,.35,.13,.005,.22))
    for tt in (116.25,116.55,116.86,118.25,118.66,119.05):
        tr.add(tt,tone(118,.07,.085,.001,.035,(1,.45)))
        tr.add(tt+.025,tone(880,.055,.045,.001,.025))
    tr.add(120.5,hum(67,.06,60))
    tr.add(120.8,pad([midi(52),midi(59),midi(64)],67,.14,3.5,7))
    tr.add(121.1,bell(midi(76),3.4,.17))
    tr.add(121.45,bell(midi(83),3.8,.11))

    starts=(143.0,149.5,155.7,161.0,166.0,170.6,175.3,180.0)
    notes=(67,69,72,74,76,79,81,83)
    tr.add(132,wheel(54,8,.50))
    for i,(tt,n) in enumerate(zip(starts,notes)):
        tr.add(tt-.18,tone(205,.04,.10,.001,.02))
        tr.add(tt,tone(76,.17,.20,.001,.14,(1,.34)))
        tr.add(tt+.17,noise(.26,.095,230+i,.15))
        tr.add(tt+.42,bell(midi(n),2.6,.09+.008*i))
    tr.add(154.4,tone(245,.055,.13,.001,.03))
    tr.add(155.0,glide(95,165,1.1,.055,.02,.25))

    tr.add(186,pad([midi(57),midi(64),midi(69)],66,.105,4,7))
    tr.add(186,flutter(21,.0,70),.8)
    for tt,f in ((188.0,2050),(191.2,2260),(195.0,1980)):
        tr.add(tt,chirp(f,True,.07))
    tr.add(198.2,tone(1320,.035,.055,.001,.02))
    tr.add(199.0,bell(midi(88),1.0,.05))
    tr.add(202.4,glide(260,390,2.8,.035,.4,.5))
    tr.add(207,wheel(22,9,1.0))
    tr.add(207,flutter(22,1.0,81),1.0)
    for k in range(13):
        tt=207.2+k*1.55
        tr.add(tt,glide(420+(k%4)*65,760+(k%5)*65,.12,.07))
        if k%2==0: tr.add(tt+.20,chirp(2150+(k%4)*180,k%3!=0,.085))
    for i,tt in enumerate((211.0,217.8,224.3)):
        tr.add(tt,tone(72+i*10,.17,.15,.001,.13,(1,.3)))
        tr.add(tt+.02,noise(.11,.10,310+i,.22))
    tr.duck(229,236,.52)
    tr.add(229.3,glide(380,220,.7,.065,.02,.5))
    tr.add(233.5,pad([midi(60),midi(67),midi(72)],19,.12,2.2,4))
    for k,n in enumerate((72,76,79,83)):
        tr.add(235.0+k*3.4,bell(midi(n),2.4,.085))
    tr.add(238.0,chirp(1700,False,.05)); tr.add(244.7,chirp(1860,True,.055))
    tr.add(247.5,flutter(4.5,.0,92),.40)

    tr.add(252,pad([midi(48),midi(55),midi(60),midi(64)],84,.155,2,6))
    beat=1.5
    for k in range(55):
        tt=252+k*beat
        tr.add(tt,tone(72,.08,.075,.002,.055,(1,.18)))
        if k%2: tr.add(tt+.75,tone(180,.032,.045,.001,.018))
    melody=(72,76,79,83,79,76,74,71,72,76,81,79,76,72,69,71,72,74,79,83,81,79)
    for k,n in enumerate(melody): tr.add(254+k*3.55,bell(midi(n),2.45,.075))
    tr.add(252,wheel(83,12,.42))
    for k in range(8): tr.add(267+k*1.45,noise(.24,.055,400+k,.08))
    for k in range(6): tr.add(288+k*2.0,tone(235+k*18,.095,.055,.002,.065))
    for k,n in enumerate((64,67,72,76,79)):
        tr.add(307+k*1.4,tone(520+k*80,.065,.06,.002,.035)); tr.add(307.1+k*1.4,bell(midi(n),1.15,.045))
    tr.add(313.0,chirp(2250,True,.045))
    tr.add(320.0,bell(midi(84),3.3,.10))
    tr.add(324.0,bell(midi(88),3.3,.09))

    tr.add(335,pad([midi(55),midi(62),midi(67),midi(71)],22,.17,2.5,4))
    for k,n in enumerate((67,71,74,79,83,79,74,71)):
        tr.add(336+k*2.15,bell(midi(n),2.0,.085))
    tr.add(341.2,chirp(2280,True,.05)); tr.add(342.7,flutter(5,.0,110),.24)
    tr.add(350.8,bell(midi(88),2.5,.07))
    tr.duck(354,361,.72)
    tr.add(356.0,glide(220,145,3.5,.075,.05,1.4))

    tr.add(357,hum(14,.105,34))
    tr.add(357,noise(14,.065,501,.0017))
    tr.add(358,pad([midi(29),midi(36),midi(41)],13,.095,3.5,4))
    for i,tt in enumerate((360.0,363.0,366.2,369.2)):
        tr.add(tt,tone(46+i*4,.7,.05,.05,.45,(1,.2)))
    tr.add(366.0,glide(620,410,.42,.06,.01,.25))
    tr.add(366.65,chirp(1780,False,.03))
    tr.add(369.0,bell(midi(60),2.6,.038))

    tr.add(371,pad([midi(48),midi(55),midi(60)],7,.085,.5,1.8))
    tr.add(372.0,bell(midi(72),3.6,.065))
    return tr


if __name__=='__main__':
    out=Path(sys.argv[1]) if len(sys.argv)>1 else ROOT/'media'/'ep01.wav'
    out.parent.mkdir(parents=True,exist_ok=True)
    print('building 6:18 soundtrack...')
    build().save(str(out))
    print(out)
