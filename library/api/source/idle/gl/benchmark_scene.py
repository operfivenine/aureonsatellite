"""Private benchmark clock: deterministic camera/effects, no user audio/input."""
from aureon_content.models import ContentEntry


class BenchmarkScene:
    def __init__(self, stage, quality='high', reactive=False):
        self.stage = stage
        self.quality = 'high'
        self.seconds = 0.0

    def advance(self, dt, frame):
        self.seconds += dt

    def uniforms(self):
        return {'u_time': self.seconds, 'u_stage': self.stage}, (0.0,) * 8


def benchmark_entry(stage):
    from aureon_benchmark_core import STAGES
    return ContentEntry(id=f'benchmark_v1_{stage}', kind='scene', name=STAGES[stage][0],
                        renderer='builtin.gl', fragment='benchmark.frag', shader_cache=True,
                        factory=lambda quality, reactive: BenchmarkScene(stage, quality, reactive))
