from .registry import ContentRegistry

_registry = None


def get_registry():
    global _registry
    if _registry is None:
        from .builtins import register_builtins
        registry = ContentRegistry()
        register_builtins(registry)
        _registry = registry
    return _registry
