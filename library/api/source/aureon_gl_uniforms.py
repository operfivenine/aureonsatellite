"""Cached OpenGL uniform upload helpers used by the fullscreen scene host.

OPT 02 contract:
- Uniform locations are resolved once per linked QOpenGLShaderProgram and cached.
- A cached -1 means the compiler optimized the uniform away; later frames skip it.
- UniformArray values use one glUniform*fv call when the active Qt/OpenGL binding
  accepts a Python float sequence.  A one-time capability failure falls back to
  cached per-element uploads without changing scene values.
- The cache is reset whenever GLSceneWidget links/replaces its program.

This module deliberately knows nothing about scene semantics.  It only moves
already-prepared numeric values into the currently-bound GL program.
"""
from __future__ import annotations


class CachedUniformUploader:
    def __init__(self):
        self._locations = {}
        self._batch_support = {}  # arity -> bool; absent means not probed yet

    def reset(self):
        self._locations.clear()
        self._batch_support.clear()

    def location(self, program, name):
        key = str(name)
        if key not in self._locations:
            self._locations[key] = int(program.uniformLocation(key))
        return self._locations[key]

    def prewarm(self, program, names):
        for name in names:
            self.location(program, name)

    def scalar(self, funcs, program, name, value):
        location = self.location(program, name)
        if location < 0:
            return False
        funcs.glUniform1f(location, float(value))
        return True

    def vector(self, funcs, program, name, value):
        values = tuple(float(component) for component in value)
        arity = len(values)
        if arity not in (2, 3, 4):
            raise ValueError(f'Unsupported uniform vector width: {arity}')
        location = self.location(program, name)
        if location < 0:
            return False
        getattr(funcs, f'glUniform{arity}f')(location, *values)
        return True

    @staticmethod
    def _array_shape(values):
        if not values:
            return 1
        first = values[0]
        if isinstance(first, (tuple, list)):
            arity = len(first)
            if arity not in (2, 3, 4):
                raise ValueError(f'Unsupported uniform array vector width: {arity}')
            return arity
        return 1

    @staticmethod
    def _flatten(values, arity):
        if arity == 1:
            return tuple(float(value) for value in values)
        flat = []
        for element in values:
            if not isinstance(element, (tuple, list)) or len(element) != arity:
                raise ValueError('Inconsistent uniform array element shape')
            flat.extend(float(component) for component in element)
        return tuple(flat)

    def array(self, funcs, program, name, values):
        values = tuple(values)
        if not values:
            return False
        arity = self._array_shape(values)
        base_name = f'{name}[0]'
        base_location = self.location(program, base_name)
        if base_location < 0:
            return False

        # Probe the Qt binding once per vector width.  PySide/QOpenGLFunctions
        # normally exposes glUniform1fv/glUniform4fv; if a platform binding does
        # not accept a Python sequence, fall back permanently for this program.
        if self._batch_support.get(arity, True):
            method = getattr(funcs, f'glUniform{arity}fv', None)
            if method is not None:
                try:
                    method(base_location, len(values), self._flatten(values, arity))
                    self._batch_support[arity] = True
                    return True
                except (TypeError, ValueError, RuntimeError, AttributeError):
                    self._batch_support[arity] = False
            else:
                self._batch_support[arity] = False

        # Cached per-element fallback.  This is still substantially cheaper than
        # the old path because uniformLocation() is never repeated per frame.
        for index, element in enumerate(values):
            location = self.location(program, f'{name}[{index}]')
            if location < 0:
                continue
            if arity == 1:
                funcs.glUniform1f(location, float(element))
            else:
                getattr(funcs, f'glUniform{arity}f')(location, *(float(v) for v in element))
        return True

    def snapshot(self):
        """Small diagnostics hook for smoke tests/logging; not used per frame."""
        return {
            'locations': len(self._locations),
            'unused': sum(1 for value in self._locations.values() if value < 0),
            'batch_support': dict(self._batch_support),
        }
