"""Stable Stellar Horizon scene with local musical events."""
import math
from .horizon_audio import HorizonAudio


class StellarHorizonGL(HorizonAudio):
    def __init__(self, quality="medium", reactive=False):
        super().__init__(quality, reactive)
        self.spectrum_enabled = False
        self.floor_bands = [0.0] * 24
        self.bass_accent = self.bass_average = 0.0

    def set_floor_spectrum_enabled(self, enabled):
        self.spectrum_enabled = bool(enabled)

    @staticmethod
    def _unit(value):
        try:
            value = float(value)
            return max(0.0, min(1.0, value)) if math.isfinite(value) else 0.0
        except (TypeError, ValueError):
            return 0.0

    def advance(self, dt, frame):
        dt = float(dt)
        if not math.isfinite(dt):
            return
        dt = max(0.0, min(0.1, dt))
        # Preserve every original event and its motion. Spectrum mode can also
        # drive the scene, consistently with the Satellite panel spectrum.
        reactive = self.reactive
        self.reactive = reactive or self.spectrum_enabled
        try:
            super().advance(dt, frame)
        finally:
            self.reactive = reactive
        active = (reactive or self.spectrum_enabled) and self.playing is not False and self.audio_mode is not False and frame is not None
        bands = list(getattr(frame, "bands", ())) if active else []
        energy = self._unit(getattr(frame, "normalized_energy", 0.0)) if active else 0.0
        shaped = []
        for value in bands:
            x = self._unit(value)
            shaped.append(min(.94, (.84*x**1.38 + .16*x**.72)*(.52+.40*energy)))
        for i in range(24):
            group = shaped[i*len(shaped)//24:max(i*len(shaped)//24+1, (i+1)*len(shaped)//24)]
            target = sum(group)/len(group) if group else 0.0
            tau = .055 if target > self.floor_bands[i] else .24
            self.floor_bands[i] += (target-self.floor_bands[i])*(1.0-math.exp(-dt/tau))
        bass = self._unit(getattr(frame, "low", 0.0)) if active else 0.0
        self.bass_average += (bass-self.bass_average)*(1.0-math.exp(-dt/.32))
        target = min(1.0, max(0.0, bass-self.bass_average)*3.0 + bass*.12)
        tau = .025 if target > self.bass_accent else .20
        self.bass_accent += (target-self.bass_accent)*(1.0-math.exp(-dt/tau))

    def uniforms(self):
        values, zones = super().uniforms()
        values["u_bass_accent"] = self.bass_accent
        for i, value in enumerate(self.floor_bands):
            values[f"u_floor_band{i}"] = value
        return values, zones
