"""Preserved Stage 2 lava appearance and motion; independent of Stellar Horizon."""
import math
from .quality import QUALITY
from audio.reactive import ReactiveAudioCore


class LavaHorizonGL:
    def __init__(self, quality="medium", reactive=False):
        self.quality = quality if quality in QUALITY or quality == "extreme" else "medium"
        self.reactive = bool(reactive)
        self.rotation = 0.0
        self.flow = 0.0
        self.orbit = 0.0
        self.camera_phase = 0.0
        self.audio_core = ReactiveAudioCore()
        self.audio_accumulator = 0.0
        self.playing = self.audio_mode = None
        self.music = [0.0] * 4
        self.panel_enabled = False
        self.panel_bars = [0.0] * 16
        self.panel_peaks = [0.0] * 16
        from aureon_content.satellite_camera import create_camera
        self._camera_driver = create_camera()

    def __getattr__(self, name):
        driver = self.__dict__.get('_camera_driver')
        if driver is None: raise AttributeError(name)
        return getattr(driver, name)

    def _legacy_camera_pose(self):
        yaw = .055 + .012 * math.sin(self.camera_phase)
        return ((-math.sin(yaw)*6.15,4.10+.035*math.sin(self.camera_phase),math.cos(yaw)*6.15),
                (0.,-.1,0.),math.degrees(2*math.atan(1/2.2)),.009*math.sin(self.camera_phase))

    def set_camera_preset(self, choice):
        driver = self._camera_driver
        if choice != 'auto' and not any(preset[0] == choice for preset in driver.camera['presets']):
            return False
        if driver.camera_preset == 'auto' and choice != 'auto':
            driver._camera_current = self._legacy_camera_pose()
            driver.camera_shot = -1
        return driver.set_camera_preset(choice)

    def begin_manual_camera(self):
        if self._camera_driver.camera_preset == 'auto':
            self._camera_driver._camera_current = self._legacy_camera_pose()
        return self._camera_driver.begin_manual_camera()

    def set_panel_spectrum_enabled(self, enabled):
        self.panel_enabled = bool(enabled)

    @staticmethod
    def _finite_unit(value):
        try:
            value = float(value)
            return max(0.0, min(1.0, value)) if math.isfinite(value) else 0.0
        except (ValueError, TypeError):
            return 0.0

    def _advance_panel_spectrum(self, dt, frame):
        active = (self.reactive or self.panel_enabled) and self.playing is not False and self.audio_mode is not False and frame is not None
        bands = list(getattr(frame, "bands", ())) if active else []
        energy = self._finite_unit(getattr(frame, "normalized_energy", 0.0)) if active else 0.0
        # Match Spectrum Bars' display curve, pooling the analyzer's log bands
        # into sixteen columns suitable for the physical width of each array.
        shaped = []
        for value in bands:
            x = self._finite_unit(value)
            shaped.append(min(0.94, (0.84*x**1.38 + 0.16*x**0.72)*(0.52+0.40*energy)))
        for i in range(16):
            if shaped:
                left = i*len(shaped)//16
                right = max(left+1, (i+1)*len(shaped)//16)
                group = shaped[left:right] or [shaped[-1]]
                target = sum(group)/len(group)
            else:
                target = 0.0
            tau = 0.04 if target >= self.panel_bars[i] else 0.13
            self.panel_bars[i] += (target-self.panel_bars[i])*(1.0-math.exp(-dt/tau))
            self.panel_peaks[i] = max(self.panel_bars[i], self.panel_peaks[i]-dt*0.65)


    def set_transport(self, playing=None, audio_mode=None):
        self.playing, self.audio_mode = playing, audio_mode

    def advance(self, dt, frame):
        dt = float(dt)
        if not math.isfinite(dt):
            return
        dt = max(0.0, min(0.1, dt))
        self.rotation = (self.rotation + dt * 0.008) % math.tau
        self.flow = (self.flow + dt * 0.035) % math.tau
        self.orbit = (self.orbit + dt * 0.012) % math.tau
        self.camera_phase = (self.camera_phase + dt * 0.12) % math.tau
        self._camera_driver.elapsed += dt
        if self._camera_driver.camera_preset != 'auto':
            self._camera_driver._camera_step(dt)
        active = self.reactive and self.playing is not False and self.audio_mode is not False and frame is not None
        self.audio_accumulator += dt
        while self.audio_accumulator >= 1.0 / 30.0:
            self.audio_core.ingest(frame if active else None)
            self.audio_core.tick()
            self.audio_accumulator -= 1.0 / 30.0
        self._advance_panel_spectrum(dt, frame)
        snap = self.audio_core.snapshot()
        targets = (snap.low, snap.mid, snap.high, snap.beat) if active else (0.0,) * 4
        for i, value in enumerate(targets):
            value = float(value)
            value = max(0.0, min(1.0, value)) if math.isfinite(value) else 0.0
            # Quick bloom, longer release: visible phrasing without binary flashes.
            target = value ** 0.75
            tau = 0.055 if target > self.music[i] else 0.28
            self.music[i] += (target - self.music[i]) * (1.0 - math.exp(-dt / tau))

    def uniforms(self):
        values = {"u_rotation": self.rotation, "u_flow": self.flow,
                  "u_orbit": self.orbit, "u_camera_phase": self.camera_phase,
                  "u_music_low": self.music[0], "u_music_mid": self.music[1],
                  "u_music_high": self.music[2], "u_music_beat": self.music[3]}
        for i in range(16):
            values[f"u_panel_bar{i}"] = self.panel_bars[i]
            values[f"u_panel_peak{i}"] = self.panel_peaks[i]
        driver = self._camera_driver
        active = driver.camera_preset != 'auto'
        if active:
            driver._publish()
            values.update({key:driver.values[key] for key in
                           ('u_camera_pos','u_camera_target','u_camera_fov','u_camera_roll')})
        else:
            pose = self._legacy_camera_pose()
            driver._camera_current = pose
            values.update(u_camera_pos=pose[0],u_camera_target=pose[1],u_camera_fov=pose[2],u_camera_roll=pose[3])
        values['u_camera_enabled'] = float(active)
        return values, (0.0,) * 8
