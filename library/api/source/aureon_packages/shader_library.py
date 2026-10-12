"""Compatibility shim for AURS Standard Library API 1.x.

New host code should import :mod:`aureon_packages.standard_library`.  This shim
is intentionally retained so existing internal imports and older regression
tests continue to resolve the same trusted library implementation.
"""
from .standard_library import *  # noqa: F401,F403
