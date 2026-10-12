"""Scene-local flight and sun pursuit; cadence is an onset heuristic, not BPM."""
import math
from collections import deque
from audio.reactive import ReactiveAudioCore
from .quality import QUALITY, CHANNELS


class OrbitalDawnGL:
    def __init__(self, quality="medium", reactive=False):
        self.quality = quality if quality in QUALITY else "medium"
        self.reactive = bool(reactive)
        self.core = ReactiveAudioCore()
        self.seconds = 0.0
        self._audio_accumulator = 0.0
        self._playing = self._audio_mode = None
        self._exposure_pressure = self._exposure_kick = 0.0
        self._bass_attack = 0.0
        self._bass_momentum = 0.0
        self._solar_drive = 0.0
        self._prev_low_drive = 0.0
        # GL6.0 Motion Pass: keep the sun channel, but give the world its own
        # slow reactive degrees of freedom so musical energy does not collapse
        # into brightness once pursuit/flare reaches its useful range.
        self._terminator_drift = 0.0
        self._orbit_motion = 0.0
        self._orbit_phase = 0.0
        self._pursuit = .10
        self._planet_rotation_speed = .42
        self._planet_rotation_phase = self._cloud_phase = self._flight_phase = 0.0
        self._glint_age = 9.0
        self._last_seed = self.core.spark_seed
        self._onsets = deque(maxlen=8)
        self._cadence = 0.0
        self._mid_cloud = self._mid_wave_phase = 0.0
        self._treble_age = 9.0
        self._treble_strength = self._prev_treble = 0.0
        self._treble_seed = 0

    def set_transport(self, playing=None, audio_mode=None):
        """Read-only presentation input; never commands the player."""
        self._playing, self._audio_mode = playing, audio_mode

    @staticmethod
    def _approach(current, target, tau, dt):
        return current + (target-current)*(1.0-math.exp(-dt/tau))

    def advance(self, dt, frame):
        dt = max(0.0, min(.1, float(dt)))
        self.seconds += dt
        self._glint_age = min(9.0, self._glint_age+dt)
        self._treble_age = min(9.0, self._treble_age+dt)
        paused = self._audio_mode is True and self._playing is False
        reactive_input = frame if self.reactive and not paused else None
        self._audio_accumulator += dt
        while self._audio_accumulator >= 1/30:
            self.core.ingest(reactive_input)
            self.core.tick()
            snap = self.core.snapshot()
            zones = [max(0.0, min(1.0, float(z))) for z in snap.zones]
            # Scene-local detail channels; do not feed pursuit or the shared core.
            detail_input = reactive_input is not None
            mid_target = max(0.0, (.65*snap.mid+.35*sum(zones[2:5])/3-.10)/.90) if detail_input else 0.0
            self._mid_cloud = self._approach(self._mid_cloud, mid_target, .16 if mid_target>self._mid_cloud else .55, 1/30)
            treble = self.core.clamp(getattr(reactive_input, "high", 0.0))
            rise = max(0.0, treble-self._prev_treble)
            if detail_input and treble>.18 and rise>.075 and self._treble_age>=.20:
                self._treble_age = 0.0
                self._treble_strength = min(1.0, rise*2.0+treble*.40)
                self._treble_seed = (self._treble_seed+1) % 4096
            self._prev_treble = treble
            mean = sum(zones)/max(1, len(zones))
            rms = math.sqrt(sum(z*z for z in zones)/max(1, len(zones)))
            raw = .58*(.65*mean+.35*rms)+.27*snap.energy+.15*snap.medium
            pressure = max(0.0, min(1.0, (raw-.18)/.82))**1.65
            kick = max(snap.beat, .8*snap.flux, .5*snap.fast)

            # Sun attack is intentionally bass-led, not cadence-led.  A fast
            # track with dense hats/snare can keep motion lively without pinning
            # the sunrise at maximum amplitude.  We detect a low-frequency rise
            # from the main low band plus the two lowest spectral zones.
            low_drive = max(0.0, min(1.0, .58*snap.low + .24*zones[0] + .18*zones[1]))
            low_rise = max(0.0, low_drive-self._prev_low_drive)
            bass_attack_target = max(
                0.0,
                min(1.0, (low_rise-.018)*4.8 + max(0.0, low_drive-.34)*.72)
            ) if detail_input else 0.0
            # Momentum needs repeated / sustained low energy, not simply tempo.
            bass_momentum_target = max(0.0, min(1.0, (low_drive-.20)/.66))**1.35 if detail_input else 0.0
            self._prev_low_drive = low_drive if detail_input else self._approach(self._prev_low_drive, 0.0, .35, 1/30)
            if self.core.spark_seed != self._last_seed and reactive_input is not None:
                if not self._onsets or self.seconds-self._onsets[-1] >= .22:
                    self._onsets.append(self.seconds)
                    self._glint_age = 0.0
            self._last_seed = self.core.spark_seed
            while self._onsets and self.seconds-self._onsets[0] > 4.0:
                self._onsets.popleft()
            cadence_target = 0.0
            if len(self._onsets) >= 3:
                interval = (self._onsets[-1]-self._onsets[0])/(len(self._onsets)-1)
                freshness = max(0.0, 1.0-(self.seconds-self._onsets[-1])/1.6)
                cadence_target = min(1.0, max(0.0, (1.0/max(.22, interval)-.65)/1.5))*freshness
            if paused:
                pressure = kick = cadence_target = 0.0
                bass_attack_target = bass_momentum_target = 0.0
                self._onsets.clear()
            self._cadence = self._approach(self._cadence, cadence_target, .6, 1/30)
            self._exposure_pressure = self._approach(self._exposure_pressure, pressure, .55 if pressure>self._exposure_pressure else 1.1, 1/30)
            self._exposure_kick = self._approach(self._exposure_kick, kick, .09 if kick>self._exposure_kick else .3, 1/30)
            self._bass_attack = self._approach(self._bass_attack, bass_attack_target, .065 if bass_attack_target>self._bass_attack else .38, 1/30)
            self._bass_momentum = self._approach(self._bass_momentum, bass_momentum_target, .34 if bass_momentum_target>self._bass_momentum else 1.05, 1/30)

            # GL6.2 Broadband Solar Drive: the visible sunrise must not disappear
            # on high/mid-heavy material simply because sub/low energy is modest.
            # Use sustained whole-spectrum activity for the base solar motion;
            # bass remains an extra cinematic push rather than the only driver.
            solar_drive_target = min(1.0,
                .52*self._exposure_pressure +
                .20*snap.medium +
                .18*snap.high +
                .10*snap.fast
            ) if detail_input else 0.0
            if paused:
                solar_drive_target = 0.0
            self._solar_drive = self._approach(
                self._solar_drive, solar_drive_target,
                .32 if solar_drive_target>self._solar_drive else .88, 1/30
            )
            ambient = self._audio_mode is False or (not self.reactive and not paused)

            # World motion is deliberately not another exposure channel.
            # GL6.3: camera orientation is fixed back to the GL5.9 transform.
            # This slow envelope now only drives the world/terminator phase;
            # transients and sustained energy never rotate or offset the camera.
            if paused:
                orbit_target = terminator_target = 0.0
            elif ambient:
                orbit_target = .18 + .05*math.sin(self.seconds*.11)
                terminator_target = .16 + .04*math.sin(self.seconds*.075+1.1)
            else:
                orbit_target = min(1.0, .52*self._exposure_pressure + .22*self._cadence + .26*self._bass_momentum)
                terminator_target = min(1.0, .62*self._exposure_pressure + .38*self._bass_momentum)
            # Deliberately long envelope for the world/terminator drift.
            # Camera orientation no longer consumes this state.
            self._orbit_motion = self._approach(self._orbit_motion, orbit_target, 1.25 if orbit_target>self._orbit_motion else 2.40, 1/30)
            self._terminator_drift = self._approach(self._terminator_drift, terminator_target, .72 if terminator_target>self._terminator_drift else 1.65, 1/30)
            if paused:
                target = 0.0
            elif ambient:
                target = .30+.16*math.sin(self.seconds*.095)
            else:
                # GL6.2: whole-spectrum musical pressure owns the base sunrise
                # motion.  Bass momentum is still a strong extra lift, while
                # cadence is deliberately restrained so dense hats/snare cannot
                # pin the sun at the ceiling as they did before GL5.9.
                target = min(1.0, .10 + .46*self._solar_drive + .08*self._cadence + .36*self._bass_momentum)
            self._pursuit = self._approach(self._pursuit, target, .62 if target>self._pursuit else 1.35, 1/30)
            speed = (.12 if paused else .42) + (0.0 if paused else .90*self._exposure_pressure+1.80*self._cadence+.45*self._exposure_kick)
            if ambient:
                speed = .68+.20*self._pursuit
            self._planet_rotation_speed = self._approach(self._planet_rotation_speed, speed, .35, 1/30)
            self._audio_accumulator -= 1/30
        step = math.radians(self._planet_rotation_speed)*dt
        self._planet_rotation_phase = (self._planet_rotation_phase+step) % math.tau
        # Mids now shear the cloud deck independently instead of only tinting a
        # wave on top of it.  Keep the base drift so idle Dawn never freezes.
        self._cloud_phase = (self._cloud_phase+step*(.18+.16*self._mid_cloud)+dt*(.002+.012*self._mid_cloud)) % math.tau
        self._flight_phase = (self._flight_phase+dt*(.028+.025*self._planet_rotation_speed)) % 1.0
        # Keep phase velocity continuous and independent of transient cadence.
        self._orbit_phase = (self._orbit_phase+dt*(.050+.070*self._orbit_motion)) % math.tau
        self._mid_wave_phase = (self._mid_wave_phase+dt*(.50+1.80*self._mid_cloud)) % math.tau

    def uniforms(self):
        snap = self.core.snapshot()
        values = {"u_"+name: max(0.0,min(1.0,float(getattr(snap,name)))) for name in CHANNELS}
        values.update({
            "u_time": (self.seconds % 7200.0)*math.tau/7200.0,
            "u_exposure_pressure": self._exposure_pressure,
            "u_exposure_kick": self._exposure_kick,
            "u_bass_attack": self._bass_attack,
            "u_bass_momentum": self._bass_momentum,
            "u_solar_drive": self._solar_drive,
            "u_terminator_drift": self._terminator_drift,
            "u_orbit_motion": self._orbit_motion,
            "u_orbit_phase": self._orbit_phase,
            "u_pursuit": self._pursuit,
            "u_pursuit_gap": 1.0-self._pursuit,
            "u_planet_rotation": self._planet_rotation_phase,
            "u_planet_rotation_speed": self._planet_rotation_speed/3.2,
            "u_cloud_phase": self._cloud_phase,
            "u_flight_phase": self._flight_phase,
            "u_cadence": self._cadence,
            "u_glint_age": self._glint_age,
            "u_flare": self.core.flare,
            "u_glint_burst": self.core.glint_burst,
            "u_spark_seed": float(self.core.spark_seed % 4096),
            "u_mid_cloud": self._mid_cloud,
            "u_mid_wave_phase": self._mid_wave_phase,
            "u_treble_age": self._treble_age,
            "u_treble_strength": self._treble_strength,
            "u_treble_seed": float(self._treble_seed),
        })
        return values, tuple(max(0.0,min(1.0,float(z))) for z in snap.zones)
