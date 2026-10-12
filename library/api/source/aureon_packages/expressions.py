"""Bounded numeric expression interpreter. Package input is never Python code."""
from .limits import LIMITS

import ast
import math
import operator

AUDIO_REACTIVE = frozenset('low mid high energy flux brightness crest beat fast medium slow presence phase'.split())
AUDIO_SPECTRUM = frozenset(f'zone{i}' for i in range(8))
# v2-only event-shaped audio controls.  They expose trusted ReactiveAudioCore
# state without giving packages code execution or mutable access to the engine.
AUDIO_EVENTS_V2 = frozenset('onset onset_strength flare glint'.split())
AUDIO = AUDIO_REACTIVE | AUDIO_SPECTRUM
AUDIO_V2 = AUDIO | AUDIO_EVENTS_V2
RUNTIME_V2 = frozenset('playing audio_mode audio_active reactive paused ambient'.split())


def _clamp(x, lo, hi):
    return max(lo, min(hi, x))


def _fract(x):
    return x - math.floor(x)


def _lerp(a, b, t):
    return a + (b-a)*t


def _smoothstep(edge0, edge1, x):
    if abs(edge1-edge0) < 1e-9:
        return 0.0
    t = _clamp((x-edge0)/(edge1-edge0), 0.0, 1.0)
    return t*t*(3.0-2.0*t)


FUNCTIONS = {
    'sin': (math.sin, 1, 1), 'cos': (math.cos, 1, 1),
    'abs': (abs, 1, 1), 'min': (min, 2, 4), 'max': (max, 2, 4),
    'clamp': (_clamp, 3, 3),
}
V2_FUNCTIONS = dict(FUNCTIONS,
    sqrt=(lambda x: math.sqrt(max(0.0, x)), 1, 1),
    exp=(lambda x: math.exp(_clamp(x, -60.0, 60.0)), 1, 1),
    floor=(math.floor, 1, 1), ceil=(math.ceil, 1, 1),
    fract=(_fract, 1, 1), pow=(lambda a,b: math.pow(max(0.0, a), _clamp(b, -16.0, 16.0)), 2, 2),
    lerp=(_lerp, 3, 3), smoothstep=(_smoothstep, 3, 3))
OPS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
       ast.Div: operator.truediv, ast.Mod: operator.mod}


class PackageError(ValueError):
    pass


def finite(value):
    value = float(value)
    if not math.isfinite(value):
        raise PackageError('Non-finite expression result')
    return max(-1000000.0, min(1000000.0, value))


class Expression:
    def __init__(self, value, signals=(), functions=None, audio_channels=None, runtime_channels=()):
        self.dependencies = set()
        self.functions = FUNCTIONS if functions is None else functions
        self.audio_channels = AUDIO if audio_channels is None else frozenset(audio_channels)
        self.runtime_channels = frozenset(runtime_channels)
        if type(value) in (int, float):
            self.tree = ast.Constant(finite(value))
            return
        if not isinstance(value, str) or not 1 <= len(value) <= LIMITS["expression_chars"]:
            raise PackageError('Expected a number or a short numeric expression')
        try:
            self.tree = ast.parse(value, mode='eval').body
        except (SyntaxError, ValueError, RecursionError) as exc:
            raise PackageError('Invalid numeric expression') from exc
        if sum(1 for _ in ast.walk(self.tree)) > LIMITS["expression_nodes"]:
            raise PackageError('Expression is too complex')
        self._validate(self.tree, set(signals), 0)

    def _validate(self, n, signals, depth):
        pending=[(n,depth)]
        while pending:
            n,depth=pending.pop()
            if depth > LIMITS['expression_depth']:
                raise PackageError('Expression nesting limit exceeded')
            if isinstance(n, ast.Constant) and type(n.value) in (int, float):
                finite(n.value)
            elif isinstance(n, ast.Name) and n.id in ('time', 'dt', 'pi'):
                pass
            elif isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name):
                if n.value.id == 'audio' and n.attr in self.audio_channels: continue
                if n.value.id == 'runtime' and n.attr in self.runtime_channels: continue
                if n.value.id == 'signal' and n.attr in signals:
                    self.dependencies.add(n.attr); continue
                raise PackageError('Unknown expression channel')
            elif isinstance(n, ast.UnaryOp) and isinstance(n.op, (ast.UAdd, ast.USub)):
                pending.append((n.operand,depth+1))
            elif isinstance(n, ast.BinOp) and type(n.op) in OPS:
                pending.extend(((n.right,depth+1),(n.left,depth+1)))
            elif isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id in self.functions:
                _,lo,hi=self.functions[n.func.id]
                if n.keywords or not lo <= len(n.args) <= hi:
                    raise PackageError('Invalid expression function arguments')
                pending.extend((arg,depth+1) for arg in reversed(n.args))
            else:
                raise PackageError('Unsupported expression operation')

    def value(self, context):
        # Small existing expressions keep the former allocation-free path.
        if isinstance(self.tree,ast.Constant): return finite(self.tree.value)
        if isinstance(self.tree,ast.Name): return finite(context[self.tree.id])
        if isinstance(self.tree,ast.Attribute): return finite(context[self.tree.value.id][self.tree.attr])
        pending=[(self.tree,False)]; values={}
        while pending:
            n,ready=pending.pop()
            if not ready:
                pending.append((n,True))
                if isinstance(n,ast.UnaryOp): pending.append((n.operand,False))
                elif isinstance(n,ast.BinOp): pending.extend(((n.right,False),(n.left,False)))
                elif isinstance(n,ast.Call): pending.extend((arg,False) for arg in reversed(n.args))
                continue
            if isinstance(n,ast.Constant): value=n.value
            elif isinstance(n,ast.Name): value=context[n.id]
            elif isinstance(n,ast.Attribute): value=context[n.value.id][n.attr]
            elif isinstance(n,ast.UnaryOp):
                value=values[n.operand]
                if isinstance(n.op,ast.USub): value=-value
            elif isinstance(n,ast.BinOp):
                a,b=values[n.left],values[n.right]
                value=0. if isinstance(n.op,(ast.Div,ast.Mod)) and abs(b)<1e-9 else finite(OPS[type(n.op)](a,b))
            else:
                try: value=finite(self.functions[n.func.id][0](*(values[arg] for arg in n.args)))
                except (ValueError,OverflowError,ZeroDivisionError): value=0.
            values[n]=value
        return finite(values[self.tree])
