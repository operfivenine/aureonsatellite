"""Local fixed-step musical events; no playback or analysis ownership."""
import math
from audio.reactive import ReactiveAudioCore
from .quality import QUALITY


class HorizonAudio:
    def __init__(self, quality="medium", reactive=False):
        self.quality = quality if quality in QUALITY else "medium"
        self.reactive = bool(reactive)
        self.core = ReactiveAudioCore()
        self.playing = self.audio_mode = None
        self.accumulator = self.rotation = self.flow = self.sky = self.light = 0.0
        self.previous_low = self.previous_high = 0.0
        self.cooldown = self.flare_cooldown = 0.0
        self.serial = 0
        self.waves = [[10.0, 0.0, 0.0] for _ in range(6)]
        self.flares = [[10.0, 0.0, 0.0] for _ in range(3)]
        self.flash = self.flash_seed = 0.0

    def set_transport(self, playing=None, audio_mode=None):
        self.playing, self.audio_mode = playing, audio_mode

    def advance(self, dt, frame):
        dt = float(dt)
        if not math.isfinite(dt):
            return
        dt = max(0.0, min(0.1, dt))
        active = self.reactive and self.playing is not False and self.audio_mode is not False and frame is not None
        self.accumulator += dt
        step = 1.0 / 60.0
        while self.accumulator >= step:
            # Core smoothing calibrated at 30 Hz, two physics steps per tick.
            self._core_phase = getattr(self, "_core_phase", 0) + 1
            if self._core_phase % 2 == 0:
                self.core.ingest(frame if active else None)
                self.core.tick()
            for event in self.waves + self.flares:
                event[0] = min(10.0, event[0] + step)
            self.cooldown = max(0.0, self.cooldown - step)
            self.flare_cooldown = max(0.0, self.flare_cooldown - step)
            low = self.core.clamp(getattr(frame, "low", 0.0)) if active else 0.0
            high = self.core.clamp(getattr(frame, "high", 0.0)) if active else 0.0
            rise = max(0.0, low - self.previous_low)
            if active and low > .20 and rise > .065 and self.cooldown <= 0:
                self.serial += 1
                strength = min(1.0, .35 + rise * 2.0 + low * .30)
                slot = max(self.waves, key=lambda e: e[0])
                if slot[0] >= 2.6:
                    slot[:] = [0.0, strength, float(self.serial % 47)]
                self.cooldown = .20
                if low > .32 and self.flare_cooldown <= 0:
                    slot = max(self.flares, key=lambda e: e[0])
                    if slot[0] >= 3.4:
                        slot[:] = [0.0, strength, .16 + (self.serial * .271) % .93]
                        self.flare_cooldown = 1.35
            self.flash *= math.exp(-step / .15)
            if active and high - self.previous_high > .08:
                self.flash = min(1.0, .25 + (high-self.previous_high)*2.0)
                self.flash_seed = float(self.serial % 47) + high * 11.0
            self.previous_low, self.previous_high = low, high
            self.accumulator -= step
        snap = self.core.snapshot()
        self.rotation = (self.rotation + dt * .008) % math.tau
        self.flow = (self.flow + dt * (.035 + .018*snap.mid)) % math.tau
        self.sky = (self.sky + dt * .060) % math.tau
        self.light = (self.light + dt * (.60 + 1.5*snap.mid)) % math.tau

    def uniforms(self):
        snap = self.core.snapshot()
        values = dict(u_rotation=self.rotation, u_flow=self.flow, u_sky=self.sky,
                      u_light=self.light, u_mid=snap.mid, u_flash=self.flash,
                      u_flash_seed=self.flash_seed)
        for prefix, events in (("wave", self.waves), ("flare", self.flares)):
            for i, event in enumerate(events):
                for field, value in zip(("age", "strength", "seed"), event):
                    values[f"u_{prefix}{i}_{field}"] = value
        return values, tuple(snap.zones)
