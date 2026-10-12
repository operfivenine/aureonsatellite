"""AURS v2 behavior validation, temporal primitives and structural loop limits.

This module is deliberately a descriptor compiler, not a scripting system.  All
package behavior is reduced to bounded expressions and a small set of trusted,
fixed-rate primitives owned by Aureon.
"""
from .limits import LIMITS, dependency_order

from dataclasses import dataclass
import math
import re

from .schema import obj, number
from .expressions import AUDIO_V2, RUNTIME_V2, Expression, PackageError, V2_FUNCTIONS


def _expr(value, signals):
    return Expression(value, signals, functions=V2_FUNCTIONS, audio_channels=AUDIO_V2, runtime_channels=RUNTIME_V2)

ARRAYS = {'u_bands': ('float',32), 'u_peaks': ('float',32), 'u_events': ('vec4',8)}
UNIFORMS = {
    'u_modes':'vec4', 'u_mode':'float', 'u_mode_age':'float',
    'u_variant':'float', 'u_playing':'float',
    # Standard camera rig.  A scene may ignore these and keep a fully custom
    # shader camera; declaring them opts into the reusable AURS camera path.
    'u_camera_pos':'vec3', 'u_camera_target':'vec3', 'u_camera_fov':'float',
    'u_camera_roll':'float', 'u_camera_distance':'float',
    'u_camera_shot':'float', 'u_camera_shot_age':'float', 'u_camera_impulse':'vec4',
}


@dataclass(frozen=True)
class V2SignalSpec:
    name: str
    kind: str
    expr: Expression
    params: dict


@dataclass(frozen=True)
class CameraShot:
    position: tuple
    target: tuple
    fov: Expression
    roll: Expression
    distance: Expression | None
    hold: float


PRESETS = {
    # The presets are intentionally scene-agnostic.  They are conveniences over
    # the same public primitives, not hidden bespoke logic.
    'bass_punch': ('envelope', 'clamp((audio.low - 0.015) * 2.4 * {gain}, 0, 1)', .055, .36),
    'beat_punch': ('envelope', 'clamp(max(audio.beat, audio.flux) * 2.1 * {gain}, 0, 1)', .012, .28),
    'air': ('envelope', 'clamp((audio.high * 2.7 + audio.brightness * 0.25) * {gain}, 0, 1)', .08, .48),
    'music_energy': ('envelope', 'clamp((audio.energy * 2.2 + audio.mid * 0.4) * {gain}, 0, 1)', .18, 1.2),
    'broadband_pressure': ('envelope', 'clamp((audio.energy * .58 + audio.medium * .27 + audio.slow * .15) * 1.8 * {gain}, 0, 1)', .28, .90),
    'slow_orbit': ('integrator', '(0.015 + audio.slow * 0.04 + audio.low * 0.012) * {gain}', math.tau, 0.0),
}


def _signal_names(signals):
    if not isinstance(signals, dict) or len(signals) > LIMITS["signals"]:
        raise PackageError('At most 4800 signals are supported')
    for key in signals:
        if not re.fullmatch(r'[a-z][a-z0-9_]{0,47}', key):
            raise PackageError('Invalid signal name')
    return tuple(signals)


def compile_signals_v2(signals):
    """Compile AURS v2's bounded temporal graph.

    Existing v1 expression/integrator/envelope descriptors remain byte-for-byte
    compatible.  New temporal types provide the reusable state needed by scenes
    such as Orbital Sun without allowing package Python code.
    """
    names = _signal_names(signals)
    compiled = {}
    for key, raw in signals.items():
        if not isinstance(raw, dict):
            raise PackageError('Signal descriptor must be an object')

        if 'preset' in raw:
            obj(raw, ('preset','gain','attack','release'))
            preset = raw.get('preset')
            if preset not in PRESETS:
                raise PackageError('Unknown AURS signal preset: '+str(preset))
            gain = number(raw.get('gain', 1.0), 0.0, 16.0)
            kind, source, a, b = PRESETS[preset]
            expr = _expr(source.format(gain=repr(gain)), names)
            if kind == 'envelope':
                params = {
                    'attack': number(raw.get('attack', a), .001, 60),
                    'release': number(raw.get('release', b), .001, 60),
                    'initial': 0.0,
                    'preset': preset,
                }
            else:
                params = {'wrap': float(a), 'initial': float(b), 'preset': preset}
            compiled[key] = V2SignalSpec(key, kind, expr, params)
            continue

        allowed = ('type','expr','rate','wrap','initial','attack','release','scale','absolute',
                   'frequency','damping','min','max','on','off','window','mode','threshold',
                   'rise','min_interval','stale','min_events')
        obj(raw, allowed)
        kind = raw.get('type', 'expression')

        if kind == 'expression':
            obj(raw, ('type','expr'), ('expr',))
            compiled[key] = V2SignalSpec(key, kind, _expr(raw['expr'], names), {'initial':0.0})
        elif kind == 'integrator':
            obj(raw, ('type','rate','wrap','initial'), ('rate',))
            compiled[key] = V2SignalSpec(key, kind, _expr(raw['rate'], names), {
                'wrap':number(raw.get('wrap',360),.001,100000),
                'initial':number(raw.get('initial',0),-100000,100000),
            })
        elif kind == 'envelope':
            obj(raw, ('type','expr','attack','release','initial'), ('expr',))
            compiled[key] = V2SignalSpec(key, kind, _expr(raw['expr'], names), {
                'attack':number(raw.get('attack',.04),.001,60),
                'release':number(raw.get('release',.3),.001,60),
                'initial':number(raw.get('initial',0),-100000,100000),
            })
        elif kind == 'derivative':
            obj(raw, ('type','expr','attack','release','scale','absolute','initial'), ('expr',))
            absolute = raw.get('absolute', False)
            if type(absolute) is not bool: raise PackageError('Derivative absolute must be boolean')
            compiled[key] = V2SignalSpec(key, kind, _expr(raw['expr'], names), {
                'attack':number(raw.get('attack',.03),.001,60),
                'release':number(raw.get('release',.25),.001,60),
                'scale':number(raw.get('scale',1.0),-1000,1000),
                'absolute':absolute,
                'initial':number(raw.get('initial',0),-100000,100000),
            })
        elif kind == 'spring':
            obj(raw, ('type','expr','frequency','damping','initial','min','max'), ('expr',))
            lo = number(raw.get('min',-100000),-100000,100000)
            hi = number(raw.get('max',100000),-100000,100000)
            if hi <= lo: raise PackageError('Spring max must exceed min')
            compiled[key] = V2SignalSpec(key, kind, _expr(raw['expr'], names), {
                'frequency':number(raw.get('frequency',1.5),.05,8.0),
                'damping':number(raw.get('damping',.85),.05,4.0),
                'initial':number(raw.get('initial',0),lo,hi), 'min':lo, 'max':hi,
            })
        elif kind == 'gate':
            obj(raw, ('type','expr','on','off','attack','release','initial'), ('expr',))
            on = number(raw.get('on',.6),-100000,100000)
            off = number(raw.get('off',.4),-100000,100000)
            if off >= on: raise PackageError('Gate requires off < on for hysteresis')
            compiled[key] = V2SignalSpec(key, kind, _expr(raw['expr'], names), {
                'on':on, 'off':off,
                'attack':number(raw.get('attack',.05),.001,60),
                'release':number(raw.get('release',.25),.001,60),
                'initial':number(raw.get('initial',0),0,1),
            })
        elif kind == 'state':
            obj(raw, ('type','rate','initial','damping','min','max','wrap'), ('rate',))
            lo = number(raw.get('min',-100000),-100000,100000)
            hi = number(raw.get('max',100000),-100000,100000)
            if hi <= lo: raise PackageError('State max must exceed min')
            wrap = raw.get('wrap', 0)
            if type(wrap) not in (int,float) or wrap < 0 or wrap > 100000:
                raise PackageError('Invalid state wrap')
            compiled[key] = V2SignalSpec(key, kind, _expr(raw['rate'], names), {
                'initial':number(raw.get('initial',0),lo,hi),
                'damping':number(raw.get('damping',0),0,60),
                'min':lo, 'max':hi, 'wrap':float(wrap),
            })
        elif kind == 'history':
            obj(raw, ('type','expr','window','mode','threshold','rise','min_interval','stale','min_events','initial'), ('expr',))
            mode = raw.get('mode','mean')
            if mode not in ('mean','max','min','interval','rate'):
                raise PackageError('Unsupported history mode')
            window = number(raw.get('window',2.0),.1,10.0)
            params = {'window':window, 'mode':mode, 'initial':number(raw.get('initial',0),-100000,100000)}
            if mode in ('interval','rate'):
                min_events=raw.get('min_events',2)
                if type(min_events) is not int or not 2 <= min_events <= 32:
                    raise PackageError('History min_events must be an integer within 2..32')
                params.update(
                    threshold=number(raw.get('threshold',.5),-100000,100000),
                    rise=number(raw.get('rise',.0),0,100000),
                    min_interval=number(raw.get('min_interval',.1),.05,5.0),
                    stale=number(raw.get('stale',min(1.6,window)),.1,10.0),
                    min_events=min_events,
                )
            compiled[key] = V2SignalSpec(key, kind, _expr(raw['expr'], names), params)
        else:
            raise PackageError('Unsupported AURS v2 signal type: '+str(kind))

    return tuple(compiled[key] for key in dependency_order(
        compiled, lambda key: compiled[key].expr.dependencies))


def _expr_vector(value, size, signals, label):
    if not isinstance(value, list) or len(value) != size:
        raise PackageError(label+' must contain '+str(size)+' values')
    return tuple(_expr(v, signals) for v in value)


def _camera_range(value, low, high, label):
    if not isinstance(value, list) or len(value) != 2:
        raise PackageError(label+' must contain [min, max]')
    a=number(value[0],low,high); b=number(value[1],low,high)
    if b <= a: raise PackageError(label+' max must exceed min')
    return (a,b)


def _camera_vec_limits(value, label):
    if value is None:
        return ((-100000.,100000.),)*3
    if not isinstance(value, list) or len(value) != 3:
        raise PackageError(label+' must contain three [min, max] ranges')
    return tuple(_camera_range(item,-100000,100000,label) for item in value)


def _camera(raw, signals, event_count):
    if raw is None: return None
    obj(raw, ('shots','mode_shots','transition','impulses','driver','easing','loop','limits','presets','manual'), ('shots',))
    shots = raw['shots']
    if not isinstance(shots,list) or not 1 <= len(shots) <= LIMITS["camera_shots"]:
        raise PackageError('Camera requires 1..800 shots')
    compiled=[]
    for shot in shots:
        obj(shot, ('position','target','fov','roll','distance','hold'), ('position','target'))
        compiled.append(CameraShot(
            _expr_vector(shot['position'],3,signals,'Camera position'),
            _expr_vector(shot['target'],3,signals,'Camera target'),
            _expr(shot.get('fov',45),signals), _expr(shot.get('roll',0),signals),
            _expr(shot['distance'],signals) if 'distance' in shot else None,
            number(shot.get('hold',6.0),0.0,120.0)))

    # Legacy mode-driven camera is retained for existing packages.  New scenes
    # should use static/timeline so camera motion remains independent of audio.
    driver=raw.get('driver','mode')
    if driver not in ('mode','static','timeline'):
        raise PackageError('Camera driver must be mode, static or timeline')
    easing=raw.get('easing','smoothstep')
    if easing not in ('linear','smoothstep','smootherstep','sine'):
        raise PackageError('Unsupported camera easing')
    loop=raw.get('loop',True)
    if type(loop) is not bool: raise PackageError('Camera loop must be boolean')

    mapping=raw.get('mode_shots',[0,0,0,0])
    if (not isinstance(mapping,list) or len(mapping)!=4 or any(type(i) is not int or not 0<=i<len(compiled) for i in mapping)):
        raise PackageError('Camera mode_shots must contain four valid shot indices')

    impulses=raw.get('impulses',[])
    if not isinstance(impulses,list) or len(impulses)>LIMITS["camera_impulses"]:
        raise PackageError('At most 800 camera impulse rules')
    rules=[]
    for rule in impulses:
        obj(rule, ('event_group','shake','roll','zoom','decay'), ('event_group',))
        group=rule['event_group']
        if type(group) is not int or not 0<=group<event_count:
            raise PackageError('Camera impulse references an unknown event group')
        rules.append(dict(group=group,
            shake=number(rule.get('shake',0),0,1), roll=number(rule.get('roll',0),0,1),
            zoom=number(rule.get('zoom',0),0,30), decay=number(rule.get('decay',.25),.03,5)))

    limits_raw=raw.get('limits',{})
    obj(limits_raw, ('position','target','distance','fov'))
    limits=dict(
        position=_camera_vec_limits(limits_raw.get('position'),'Camera position limits'),
        target=_camera_vec_limits(limits_raw.get('target'),'Camera target limits'),
        distance=_camera_range(limits_raw.get('distance',[.05,100000.]),.01,100000.,'Camera distance limits'),
        fov=_camera_range(limits_raw.get('fov',[10.,120.]),1.,179.,'Camera FOV limits'),
    )

    presets_raw=raw.get('presets',[])
    if not isinstance(presets_raw,list) or len(presets_raw)>LIMITS["camera_presets"]:
        raise PackageError('Camera presets requires at most 800 entries')
    presets=[]; ids=set()
    for item in presets_raw:
        obj(item,('id','name','shot'),('id','name','shot'))
        ident=item['id']; names=item['name']; shot=item['shot']
        if not isinstance(ident,str) or not re.fullmatch(r'[a-z][a-z0-9_]{0,31}',ident) or ident in ('auto','manual') or ident in ids:
            raise PackageError('Invalid or duplicate camera preset id')
        obj(names,('en','ru'),('en',))
        if any(not isinstance(v,str) or not v.strip() or len(v)>48 or any(ord(c)<32 for c in v) for v in names.values()):
            raise PackageError('Invalid camera preset name')
        if type(shot) is not int or not 0<=shot<len(compiled):
            raise PackageError('Camera preset shot is out of range')
        ids.add(ident)
        presets.append((ident,names['en'].strip(),names.get('ru',names['en']).strip(),shot))
    manual=None
    if 'manual' in raw:
        config=obj(raw['manual'],('yaw','pitch','distance'),('yaw','pitch','distance'))
        if not presets:raise PackageError('Manual camera requires camera presets')
        manual=dict(yaw=_camera_range(config['yaw'],-175,175,'Manual yaw'),
                    pitch=_camera_range(config['pitch'],-80,80,'Manual pitch'),
                    distance=_camera_range(config['distance'],.05,100000,'Manual distance'))
    return dict(manual=manual, presets=tuple(presets), shots=tuple(compiled), mode_shots=tuple(mapping), driver=driver,
                transition=number(raw.get('transition',1.1),.05,30), easing=easing,
                loop=loop, limits=limits, impulses=tuple(rules))


def behavior(data, signals=()):
    config = obj(data.get('behavior', {}), ('seed','modes','events','camera'))
    seed = config.get('seed', 17)
    if type(seed) is not int or not 0 <= seed <= 65535: raise PackageError('Invalid scene seed')

    modes = obj(config.get('modes', {}), ('active_on','active_off','peak_on','peak_off','dwell','peak_hold','recover','blend','source'))
    defaults = dict(active_on=.22, active_off=.12, peak_on=.63, peak_off=.42,
                    dwell=2.5, peak_hold=2.0, recover=3.0, blend=.8)
    mode_values = {k:number(modes.get(k,v), .01 if k in ('dwell','peak_hold','recover','blend') else 0,
                     30 if k in ('dwell','peak_hold','recover','blend') else 1) for k,v in defaults.items()}
    if not mode_values['active_off'] < mode_values['active_on'] < mode_values['peak_off'] < mode_values['peak_on']:
        raise PackageError('Mode thresholds must have separate hysteresis ranges')
    mode_values['source'] = _expr(modes['source'],signals) if 'source' in modes else None

    events = config.get('events', [])
    if not isinstance(events,list) or len(events)>LIMITS["event_types"]: raise PackageError('At most 400 event types')
    compiled=[]; slots=0
    for spec in events:
        obj(spec, ('channel','source','threshold','rise','cooldown','duration','slots','edge','strength'))
        channel=spec.get('channel'); source=spec.get('source')
        if (channel is None) == (source is None):
            raise PackageError('Event requires exactly one channel or source expression')
        if channel is not None and channel not in AUDIO_V2: raise PackageError('Unknown event audio channel')
        count=spec.get('slots',2)
        if type(count) is not int or not 1<=count<=LIMITS["event_slots"]: raise PackageError('Invalid event slot count')
        slots+=count
        if slots>LIMITS["event_slots"]: raise PackageError('At most 800 live event slots')
        edge=spec.get('edge','rise')
        if edge not in ('rise','fall','level'): raise PackageError('Unsupported event edge mode')
        compiled.append(dict(channel=channel, source=_expr(source,signals) if source is not None else None,
            strength=_expr(spec['strength'],signals) if 'strength' in spec else None,
            edge=edge, slots=count, threshold=number(spec.get('threshold',.25),-100000,100000),
            rise=number(spec.get('rise',.035),0,100000), cooldown=number(spec.get('cooldown',.45),.05,30),
            duration=number(spec.get('duration',3),.1,30)))

    return dict(seed=seed,modes=mode_values,events=tuple(compiled),
                camera=_camera(config.get('camera'),signals,len(compiled)))


def loop_limits(clean,quality):
    loops=list(re.finditer(r'\bfor\s*\(([^)]*)\)',clean))
    if len(loops)!=len(re.findall(r'\bfor\b',clean)) or len(loops)>LIMITS["v2_loops"]:
        raise PackageError('Too many or malformed shader loops')
    ranges=[]
    for item in loops:
        m=re.fullmatch(r'\s*int\s+([a-zA-Z_]\w*)\s*=\s*0\s*;\s*\1\s*<\s*(\d+|[A-Z][A-Z0-9_]*)\s*;\s*(?:\1\s*\+\+|\+\+\s*\1)\s*',item[1])
        if not m: raise PackageError('AURS v2 requires bounded integer loops')
        bounds=[int(m[2])] if m[2].isdigit() else [q.get(m[2],0) for q in quality.values()]
        if not all(1<=x<=LIMITS["loop_iterations"] for x in bounds): raise PackageError('Invalid shader loop bound')
        start=item.end()
        while start<len(clean) and clean[start].isspace(): start+=1
        if start>=len(clean) or clean[start]!='{': raise PackageError('Shader loop body must use braces')
        depth=1; end=start+1
        while end<len(clean) and depth:
            if clean[end]=='{': depth+=1
            elif clean[end]=='}': depth-=1
            end+=1
        if depth: raise PackageError('Unclosed shader loop')
        body=clean[start+1:end-1]
        if re.search(r'\b'+re.escape(m[1])+r'\s*(?:\+\+|--|[+*/%-]?=(?!=))|(?:\+\+|--)\s*\b'+re.escape(m[1])+r'\b',body):
            raise PackageError('Loop counters may not be modified in the loop body')
        ranges.append((item.start(),end,max(bounds)))
    total=0
    for start,end,bound in ranges:
        enclosing=[x for x in ranges if x[0]<start and end<=x[1]]
        if len(enclosing)+1>LIMITS["loop_depth"]: raise PackageError('Shader loop nesting limit exceeded')
        cost=bound
        for outer in enclosing: cost*=outer[2]
        total+=cost
    if total>LIMITS["v2_loop_budget"]: raise PackageError('Shader structural loop budget exceeded')
