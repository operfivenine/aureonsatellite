"""AURP Standard Library foundation.

This module is trusted host code for declarative ``projection.canvas.v1``
packages.  AURP packages remain JSON-only and cannot execute Python.  The
foundation deliberately starts small: it establishes a versioned public
library id and a namespaced expression-helper surface that can grow without
changing the base AURP expression contract.

Author-facing opt-in (experimental foundation)::

    "libraries": ["aurp.standard"]

The package manifest must also require
``projection.standard_library.experimental.v1`` while this contract is in
foundation status.
"""
from __future__ import annotations

import math

from .expressions import FUNCTIONS, PackageError

AURP_STANDARD_LIBRARY_ID = "aurp.standard"
AURP_STANDARD_LIBRARY_API_VERSION = "1.0-foundation"
AURP_STANDARD_LIBRARY_API_MAJOR = 1
AURP_STANDARD_LIBRARY_STATUS = "experimental"
AURP_STANDARD_LIBRARY_FEATURE = "projection.standard_library.experimental.v1"
AURP_STANDARD_LIBRARY_NAMESPACE = "aur_"


def _sat(x):
    return max(0.0, min(1.0, x))


def _lerp(a, b, t):
    return a + (b - a) * t


def _smoothstep(edge0, edge1, x):
    if abs(edge1 - edge0) < 1e-9:
        return 0.0
    t = _sat((x - edge0) / (edge1 - edge0))
    return t * t * (3.0 - 2.0 * t)


def _fract(x):
    return x - math.floor(x)


def _remap(x, a, b, c, d):
    if abs(b - a) < 1e-9:
        return c
    return _lerp(c, d, _sat((x - a) / (b - a)))


# Keep helpers namespaced from day one.  This leaves the base expression API
# untouched and gives the library room to evolve independently.
AURP_STANDARD_EXPRESSION_FUNCTIONS = {
    "aur_sat": (_sat, 1, 1),
    "aur_lerp": (_lerp, 3, 3),
    "aur_smoothstep": (_smoothstep, 3, 3),
    "aur_fract": (_fract, 1, 1),
    "aur_remap": (_remap, 5, 5),
}

AURP_STANDARD_LIBRARY_V1_SYMBOLS = tuple(sorted(AURP_STANDARD_EXPRESSION_FUNCTIONS))


def public_libraries() -> tuple[str, ...]:
    return (AURP_STANDARD_LIBRARY_ID,)


def available_libraries() -> tuple[str, ...]:
    return public_libraries()


def resolve_libraries(value) -> tuple[str, ...]:
    """Validate AURP library imports and preserve deterministic order."""
    if value is None:
        return ()
    if not isinstance(value, list) or len(value) > 16 or any(not isinstance(x, str) for x in value):
        raise PackageError("AURP libraries must be a list of at most 16 names")
    if len(set(value)) != len(value):
        raise PackageError("AURP libraries must not contain duplicates")
    unknown = [name for name in value if name not in available_libraries()]
    if unknown:
        raise PackageError("Unknown AURP library: " + ", ".join(sorted(unknown)))
    return tuple(value)


def expression_functions(libraries: tuple[str, ...]):
    """Return the safe expression function table for a resolved import set."""
    functions = dict(FUNCTIONS)
    if AURP_STANDARD_LIBRARY_ID in libraries:
        functions.update(AURP_STANDARD_EXPRESSION_FUNCTIONS)
    return functions
