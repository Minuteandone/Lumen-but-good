"""Small procedural audio toolkit for the cinematic LUMEN remake."""
from __future__ import annotations
import math, wave
import numpy as np

SR=32000


def env(n, attack=.01, release=.2):
    e=np.ones(n,dtype=np.float32)
    na=min(n,max(1,int(attack*SR))); nr=min(n,max(1,int(release*SR)))
    e[:na]=np.linspace(0,1,na,dtype=np.float32)
    e[-nr:]=np.minimum(e[-nr:],np.linspace(1,0,nr,dtype=np.float32))
    return e


def tone(freq,dur,amp=.3,attack=.01,release=.15,harmonics=(1.0,)):
    t=np.arange(int(dur*SR),dtype=np.float32)/SR
    s=np.zeros_like(t)
    for i,h in enumerate(harmonics,1): s += np.sin(2*np.pi*freq*i*t)*(h/i)
    return s*env(len(s),attack,release)*amp


def glide(f0,f1,dur,amp=.25,attack=.005,release=.12):
    n=int(dur*SR); t=np.arange(n,dtype=np.float32)/SR
    f=f0+(f1-f0)*(t/dur)
    ph=2*np.pi*np.cumsum(f,dtype=np.float64)/SR
    return np.sin(ph).astype(np.float32)*env(n,attack,release)*amp


def noise(dur,amp=.15,seed=1,lowpass=.03):
    rr=np.random.RandomState(seed); x=rr.randn(int(dur*SR)).astype(np.float32)
    y=np.empty_like(x); v=0.0
    for i,z in enumerate(x):
        v += lowpass*(float(z)-v); y[i]=v
    m=max(1e-6,float(np.max(np.abs(y)))); return y/m*amp


def bell(freq,dur=1.8,amp=.25):
    t=np.arange(int(dur*SR),dtype=np.float32)/SR
    s=(np.sin(2*np.pi*freq*t)+.35*np.sin(2*np.pi*freq*2.77*t)*np.exp(-t*5)+.18*np.sin(2*np.pi*freq*5.21*t)*np.exp(-t*9))
    return (s*np.exp(-t*2.35)*env(len(t),.002,.08)*amp).astype(np.float32)


def pad(freqs,dur,amp=.12,attack=2.0,release=3.0):
    t=np.arange(int(dur*SR),dtype=np.float32)/SR
    s=np.zeros_like(t)
    for f in freqs:
        s += np.sin(2*np.pi*f*t)+.12*np.sin(2*np.pi*f*2*t)
    s/=max(1,len(freqs)); return s*env(len(s),attack,release)*amp


def midi(n): return 440.0*2**((n-69)/12)


class Track:
    def __init__(self,duration):
        self.duration=float(duration)
        self.a=np.zeros(int((duration+.5)*SR),dtype=np.float32)
    def add(self,t0,sig,gain=1.0):
        i=max(0,int(t0*SR)); j=min(len(self.a),i+len(sig))
        if j>i:self.a[i:j]+=sig[:j-i]*gain
    def duck(self,t0,t1,amount=.5):
        a=max(0,int(t0*SR)); b=min(len(self.a),int(t1*SR)); self.a[a:b]*=amount
    def save(self,path):
        a=np.tanh(self.a*.95)
        peak=max(1e-6,float(np.max(np.abs(a)))); a=a/peak*.88
        pcm=(a*32767).astype(np.int16)
        with wave.open(path,"wb") as w:
            w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
