"""Storm Tornado GL scene state and Reactive Core bridge.

This module owns only bounded scene time and small cinematic envelopes.  It does
not touch playback, Qt or OpenGL resources.  The fragment shader renders the
storm itself; this class translates Aureon's existing ReactiveAudioCore into
stable macro/micro controls and event ages for lightning.
"""
import math

from audio.reactive import ReactiveAudioCore
from .quality import QUALITY, CHANNELS


class StormTornadoGL:
    def __init__(self, quality="medium", reactive=False):
        self.quality = quality if quality in QUALITY else "medium"
        self.reactive = bool(reactive)
        self.core = ReactiveAudioCore()
        self.seconds = 0.0
        self._audio_accumulator = 0.0

        # Sustained envelopes.  Macro pressure should feel heavy rather than
        # twitchy; vortex/wind can answer mids faster while fine electricity is
        # left to the Core's fast/high/flux controls.
        self._storm_pressure = 0.18
        self._vortex_drive = 0.20
        self._wind_drive = 0.18

        # Electrical charge is a scene-local leaky accumulator.  Sustained low
        # and low-mid energy (including bass-guitar weight) builds tension over
        # several seconds; a musical onset can release that stored energy later.
        self._storm_charge = 0.0
        self._charge_pulse = 0.0
        self._charge_pulse_cooldown = 0.0
        self._preflash = 0.0
        self._pending_major_strike = False
        self._pending_major_delay = 0.0
        self._pending_major_seed = 11.0
        self._pending_major_power = 0.0

        # Event clocks.  A new Core onset starts one major cloud-to-ground bolt;
        # fast/high transient rises can start a short secondary branch burst.
        self._major_lightning_age = 9.0
        self._minor_lightning_age = 9.0
        self._major_lightning_seed = 11.0
        self._minor_lightning_seed = 37.0
        self._major_strike_power = 0.0
        self._last_spark_seed = self.core.spark_seed
        self._last_glint_burst = 0.0
        self._event_serial = 0

    @staticmethod
    def _smooth(current, target, attack, release):
        amount = attack if target > current else release
        return current + (target - current) * amount

    def advance(self, dt, frame):
        dt = max(0.0, min(0.1, float(dt)))
        self.seconds += dt
        self._major_lightning_age = min(9.0, self._major_lightning_age + dt)
        self._minor_lightning_age = min(9.0, self._minor_lightning_age + dt)
        self._charge_pulse_cooldown = max(0.0, self._charge_pulse_cooldown - dt)

        # Pre-flash is a real scene-state delay, never a sleep/timer stall.
        # The accepted GL7.4 bolt renderer only begins after this short warning.
        if self._pending_major_strike:
            self._pending_major_delay -= dt
            if self._pending_major_delay <= 0.0:
                self._major_lightning_age = 0.0
                self._major_lightning_seed = float(self._pending_major_seed)
                self._major_strike_power = max(0.0, min(1.0, float(self._pending_major_power)))
                self._storm_charge = max(0.0, min(1.0, self._storm_charge * 0.22))
                self._pending_major_strike = False
                self._pending_major_delay = 0.0
                self._preflash = 0.0

        self._audio_accumulator += dt

        while self._audio_accumulator >= 1.0 / 30.0:
            self.core.ingest(frame if self.reactive else None)
            self.core.tick()
            snapshot = self.core.snapshot()

            zones = tuple(max(0.0, min(1.0, float(v))) for v in snapshot.zones)
            zone_low = sum(zones[:3]) / 3.0 if len(zones) >= 3 else snapshot.low
            zone_mid = sum(zones[2:6]) / 4.0 if len(zones) >= 6 else snapshot.mid
            zone_high = sum(zones[5:]) / 3.0 if len(zones) >= 8 else snapshot.high
            # Low-mid explicitly spans the lower spectral zones rather than only
            # the analyzer's broad low channel.  This lets sustained bass guitar
            # and dense rock riffs charge the storm even without sub-bass hits.
            zone_low_mid = sum(zones[1:4]) / 3.0 if len(zones) >= 4 else 0.5 * (snapshot.low + snapshot.mid)

            # Low/energy move the mass of the storm.  Mid controls visible
            # rotational/turbulent structure.  High does not make the funnel
            # bigger; it is reserved for rain/debris/electric detail.
            pressure_target = max(0.0, min(1.0,
                0.34 * snapshot.low
                + 0.30 * snapshot.energy
                + 0.18 * snapshot.medium
                + 0.18 * zone_low
            ))
            vortex_target = max(0.0, min(1.0,
                0.22 * snapshot.low
                + 0.42 * snapshot.mid
                + 0.20 * zone_mid
                + 0.16 * snapshot.energy
            ))
            wind_target = max(0.0, min(1.0,
                0.28 * snapshot.mid
                + 0.24 * snapshot.high
                + 0.22 * snapshot.fast
                + 0.14 * snapshot.flux
                + 0.12 * zone_high
            ))

            self._storm_pressure = self._smooth(self._storm_pressure, pressure_target, 0.16, 0.030)
            self._vortex_drive = self._smooth(self._vortex_drive, vortex_target, 0.24, 0.055)
            self._wind_drive = self._smooth(self._wind_drive, wind_target, 0.32, 0.080)

            # Storm Charge System.  This is intentionally an integrator rather
            # than a conventional attack/release envelope: sustained aggression
            # accumulates electrical tension and quiet passages leak it away.
            charge_drive = max(0.0, min(1.0,
                0.42 * snapshot.low
                + 0.30 * zone_low_mid
                + 0.16 * snapshot.energy
                + 0.12 * self._storm_pressure
            ))
            charge_gain = max(0.0, charge_drive - 0.18)
            charge_step = 1.0 / 30.0
            self._storm_charge += charge_step * (
                charge_gain * 0.56
                - (1.0 - charge_drive) * self._storm_charge * 0.16
            )
            self._storm_charge = max(0.0, min(1.0, self._storm_charge))

            # Short intracloud pulse envelopes die quickly; charge itself does not.
            self._charge_pulse *= 0.78
            self._preflash *= 0.58

            new_seed = self.core.spark_seed != self._last_spark_seed
            # Repeated low/low-mid attacks can also charge the cell in steps.
            # This preserves musical behaviour for kick/bass-driven material that
            # has strong rhythmic accents but little sustained sub-bass.
            if new_seed:
                event_low_mass = max(0.0, min(1.0, 0.58 * snapshot.low + 0.42 * zone_low_mid))
                self._storm_charge = min(1.0, self._storm_charge + 0.22 * event_low_mass * (0.65 + 0.35 * snapshot.energy))

            pulse_accent = max(snapshot.flux, snapshot.fast, snapshot.beat * 0.85)
            if new_seed and self._storm_charge > 0.50 and self._charge_pulse_cooldown <= 0.0 and pulse_accent > 0.18:
                charge_norm = max(0.0, min(1.0, (self._storm_charge - 0.50) / 0.50))
                self._charge_pulse = max(self._charge_pulse, min(1.0, 0.44 + 0.46 * charge_norm + 0.18 * pulse_accent))
                self._charge_pulse_cooldown = 0.80 - 0.45 * charge_norm

            # A major strike is no longer an immediate response to one transient.
            # First the storm must be electrically charged; then a fresh onset
            # starts a ~110 ms pre-flash before the accepted bolt renderer fires.
            major_interval = 2.2 + 1.3 * (1.0 - self._storm_pressure)
            event_score = (
                0.45 * snapshot.beat
                + 0.35 * snapshot.flux
                + 0.20 * snapshot.fast
            )
            if (
                new_seed
                and not self._pending_major_strike
                and self._storm_charge >= 0.72
                and self._major_lightning_age >= major_interval
                and event_score > 0.30
                and snapshot.energy > 0.10
            ):
                self._event_serial += 1
                self._pending_major_strike = True
                self._pending_major_delay = 0.11
                self._preflash = 1.0
                self._pending_major_seed = float((self.core.spark_seed * 17 + self._event_serial * 31) % 4093)
                strike_power = (
                    0.26 * snapshot.low
                    + 0.20 * snapshot.energy
                    + 0.16 * snapshot.flux
                    + 0.14 * snapshot.high
                    + 0.12 * snapshot.crest
                    + 0.08 * snapshot.fast
                    + 0.04 * zone_low
                )
                self._pending_major_power = max(0.0, min(1.0, float(strike_power)))

            glint = float(self.core.glint_burst)
            glint_rise = glint > max(0.30, self._last_glint_burst + 0.10)
            if (
                glint_rise
                and not self._pending_major_strike
                and self._minor_lightning_age > 1.75
                and self._major_lightning_age > .75
            ):
                self._event_serial += 1
                self._minor_lightning_age = 0.0
                self._minor_lightning_seed = float((self.core.spark_seed * 29 + self._event_serial * 19 + 71) % 4093)
                # A minor discharge only bleeds the accumulator once the cell is
                # genuinely charged; ordinary GL7.4 intracloud texture must not
                # prevent the storm from ever reaching a major release.
                if self._storm_charge >= 0.72:
                    self._storm_charge = max(0.0, min(1.0, self._storm_charge * 0.72))

            self._last_spark_seed = self.core.spark_seed
            self._last_glint_burst = glint
            self._audio_accumulator -= 1.0 / 30.0

    def uniforms(self):
        snapshot = self.core.snapshot()
        values = {
            "u_" + name: max(0.0, min(1.0, float(getattr(snapshot, name))))
            for name in CHANNELS
        }
        values.update({
            "u_brightness": max(0.0, min(1.0, float(snapshot.brightness))),
            "u_crest": max(0.0, min(1.0, float(snapshot.crest))),
            "u_presence": max(0.0, min(1.0, float(snapshot.presence))),
            "u_phase_audio": float(snapshot.phase),
            "u_flare": max(0.0, min(1.0, float(self.core.flare))),
            "u_sky_flash": max(0.0, min(1.0, float(self.core.sky_flash))),
            "u_glint_burst": max(0.0, min(1.0, float(self.core.glint_burst))),
            "u_spark_seed": float(self.core.spark_seed % 4096),
            "u_storm_pressure": max(0.0, min(1.0, float(self._storm_pressure))),
            "u_vortex_drive": max(0.0, min(1.0, float(self._vortex_drive))),
            "u_wind_drive": max(0.0, min(1.0, float(self._wind_drive))),
            "u_storm_charge": max(0.0, min(1.0, float(self._storm_charge))),
            "u_charge_pulse": max(0.0, min(1.0, float(self._charge_pulse))),
            "u_preflash": max(0.0, min(1.0, float(self._preflash))),
            "u_major_lightning_age": max(0.0, min(9.0, float(self._major_lightning_age))),
            "u_major_lightning_seed": float(self._major_lightning_seed),
            "u_major_strike_power": max(0.0, min(1.0, float(self._major_strike_power))),
            "u_minor_lightning_age": max(0.0, min(9.0, float(self._minor_lightning_age))),
            "u_minor_lightning_seed": float(self._minor_lightning_seed),
            # Bounded seconds are easier to author for cinematic motion than a
            # multi-hour raw float and retain ample precision indefinitely.
            "u_storm_time": float(self.seconds % 600.0),
            "u_time": (self.seconds % 7200.0) * math.tau / 7200.0,
        })
        zones = tuple(max(0.0, min(1.0, float(v))) for v in snapshot.zones)
        return values, zones
