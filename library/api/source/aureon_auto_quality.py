"""Measured quality policy and bounded, atomic local profile storage (no Qt)."""
from collections import deque
import hashlib
import json
import math
import os
from pathlib import Path
import tempfile
import time

PROTOCOL = 1
LEVELS = ('lowest', 'low', 'medium', 'high')
GPU_BUDGET_MS = 14.0  # Reserve time for native-resolution artwork/UI/composition.
FRAME_BUDGET_MS = 17.0


def percentile(values):
    clean = sorted(float(x) for x in values if isinstance(x, (int, float)) and not isinstance(x, bool)
                   and math.isfinite(x) and x >= 0)
    return clean[min(len(clean)-1, math.ceil(.95*len(clean))-1)] if clean else None


class Samples:
    def __init__(self):
        self.values = {key: deque(maxlen=600) for key in ('gpu_scene', 'composition', 'cpu')}

    def add(self, key, value):
        if key in self.values and isinstance(value, (int, float)) and math.isfinite(value) and value >= 0:
            self.values[key].append(value)

    def result(self):
        return {key: {'p95': percentile(values), 'samples': len(values)} for key, values in self.values.items()}


def valid_metric(row, name, minimum):
    item = row.get(name, {}) if isinstance(row, dict) else {}
    value = item.get('p95') if isinstance(item, dict) else None
    count = item.get('samples', 0) if isinstance(item, dict) else 0
    if (type(count) is int and count >= minimum and type(value) in (int, float)
            and math.isfinite(value) and value >= 0):
        return float(value)
    return None


def passes(row, raster=False):
    if raster:
        cpu = valid_metric(row, 'cpu', 30)
        return cpu is not None and cpu <= GPU_BUDGET_MS
    frame = valid_metric(row, 'composition', 30)
    gpu = valid_metric(row, 'gpu_scene', 8)
    if isinstance(row, dict) and (row.get('gpu_scene') or {}).get('samples', 0) and gpu is None:
        return False
    # On contexts without timer queries, the real unsynchronised frame interval
    # is the fallback. An absent counter is never interpreted as zero work.
    return frame is not None and frame <= FRAME_BUDGET_MS and (gpu is None or gpu <= GPU_BUDGET_MS)


def choose(results, raster=False):
    return next((level for level in reversed(LEVELS) if passes(results.get(level), raster)), 'lowest')


def candidate_valid(row, raster=False):
    name = 'cpu' if raster else 'composition'
    if valid_metric(row, name, 30) is not None:
        return True
    # Slow higher tiers cannot supply thirty frames in the measurement window.
    # They still provide evidence of failure; don't discard a good lower tier.
    slow = valid_metric(row, name, 3)
    return slow is not None and slow > 25


def overloaded(row, raster=False):
    if raster:
        cpu = valid_metric(row, 'cpu', 3)
        return cpu is not None and cpu > 19.0
    gpu = valid_metric(row, 'gpu_scene', 3)
    frame = valid_metric(row, 'composition', 3)
    return (gpu is not None and gpu > 19.0) or (frame is not None and frame > 25.0)


class Downshift:
    """Two bad, independent two-second windows; no speculative promotions."""
    def __init__(self):
        self.bad = 0

    def observe(self, quality, row, raster=False):
        self.bad = self.bad + 1 if overloaded(row, raster) else 0
        if self.bad < 2 or quality not in LEVELS or quality == 'lowest':
            return quality
        self.bad = 0
        # Raster presets above Lowest are identical, so skip those redundant steps.
        return 'lowest' if raster else LEVELS[LEVELS.index(quality)-1]


def identity(device, style, resolution, advanced, revision='', context=None):
    if not isinstance(device, dict) or not device.get('renderer'):
        return None
    payload = {'protocol': PROTOCOL, 'device': {key: device.get(key, '') for key in
               ('renderer', 'vendor', 'version', 'glsl_version')}, 'scene': style,
               'revision': revision, 'resolution': list(resolution), 'advanced': advanced,
               'context': context or {}}
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def scene_revision(entry):
    """Builtin shader changes invalidate profiles; AURS already carries a digest."""
    if entry is None:
        return ''
    if entry.source != 'builtin':
        return str(entry.revision)
    from aureon_paths import resource_path
    path = resource_path('idle', 'gl', 'shaders', entry.fragment)
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        # Raster renderer changes are tied to this quality protocol.
        return 'builtin-raster-v1'


def memory_allows(device, size, quality, advanced=None):
    """Supplementary FBO budget only; shared/unknown VRAM stays unknown."""
    memory = device.get('dedicated_memory_mb') if isinstance(device, dict) else None
    if type(memory) not in (int, float) or not math.isfinite(memory) or memory <= 0:
        return True
    from idle.render_quality import background_size
    w, h = background_size(*size, quality, resolution=(advanced or {}).get('resolution'))
    # Conservative allowance for color, depth, AA and reflection targets.
    return w*h*64 <= memory*1024*1024*.25


class ProfileStore:
    def __init__(self, path):
        self.path = Path(path)
        self.rows = {}
        try:
            if self.path.stat().st_size > 1024*1024:
                return
            value = json.loads(self.path.read_text(encoding='utf-8'))
            rows = value.get('profiles', {}) if isinstance(value, dict) and value.get('protocol') == PROTOCOL else {}
            if isinstance(rows, dict):
                for key, row in list(rows.items())[-256:]:
                    if (isinstance(key, str) and len(key) == 64 and isinstance(row, dict)
                            and row.get('quality') in LEVELS and type(row.get('time')) in (int, float)
                            and math.isfinite(row['time']) and 0 <= time.time()-row['time'] <= 90*86400):
                        self.rows[key] = row
        except (OSError, ValueError, TypeError):
            pass

    def quality(self, key):
        return self.rows.get(key, {}).get('quality') if key else None

    def save(self, key, quality, source, results=None):
        if not key or quality not in LEVELS:
            return False
        row = {'quality': quality, 'time': time.time(), 'source': source}
        if results is not None:
            row['measurements'] = results
        updated = {**self.rows, key: row}
        updated = dict(sorted(updated.items(), key=lambda pair: pair[1]['time'])[-256:])
        temporary = None
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=self.path.parent,
                                             suffix='.tmp', delete=False) as stream:
                temporary = stream.name
                json.dump({'protocol': PROTOCOL, 'profiles': updated}, stream, allow_nan=False)
            os.replace(temporary, self.path)
            self.rows = updated
            return True
        except (OSError, ValueError, TypeError):
            return False
        finally:
            if temporary:
                try:
                    os.unlink(temporary)
                except OSError:
                    pass
