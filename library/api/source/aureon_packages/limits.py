"""WIN06: package capacity ceilings are exactly 100x the WIN05 profile."""

LIMIT_MULTIPLIER = 100
BASE_LIMITS = {
    'archive_bytes': 8 * 1024 * 1024,
    'expanded_bytes': 16 * 1024 * 1024,
    'resource_bytes': 4 * 1024 * 1024,
    'json_bytes': 512 * 1024,
    'archive_entries': 72,
    'signals': 48,
    'expression_chars': 256,
    'expression_nodes': 96,
    'expression_depth': 12,
    'shader_bytes': 128 * 1024,
    'quality_defines': 16,
    'uniforms': 48,
    'textures': 4,
    'image_axis': 2048,
    'texture_bytes': 32 * 1024 * 1024,
    'lights': 4,
    'camera_shots': 8,
    'camera_presets': 8,
    'camera_impulses': 8,
    'event_types': 4,
    'event_slots': 8,
    'v1_loops': 8,
    'v1_loop_budget': 4096,
    'v2_loops': 32,
    'v2_loop_budget': 32768,
    'loop_iterations': 256,
    'loop_depth': 4,
    'canvas_axis': 512,
    'supersample': 3,
    'raster_scale': 4,
    'projection_nodes': 128,
    'projection_depth': 8,
    'holograms': 2,
    'polygon_points': 128,
    'projection_image_pixels': 4 * 1024 * 1024,
}
LIMITS = {name: value * LIMIT_MULTIPLIER for name, value in BASE_LIMITS.items()}


def dependency_order(values, dependencies):
    """Iterative topological order: 4800 signals must not hit Python recursion."""
    # Imported lazily to avoid the Expression -> limits -> Expression cycle.
    from .expressions import PackageError
    state = {}
    ordered = []
    for key in values:
        if state.get(key) == 2:
            continue
        state[key] = 1
        stack = [(key, iter(dependencies(key)))]
        while stack:
            current, pending = stack[-1]
            try:
                dep = next(pending)
            except StopIteration:
                state[current] = 2
                ordered.append(current)
                stack.pop()
                continue
            if state.get(dep) == 1:
                raise PackageError('Cyclic signal references')
            if state.get(dep) != 2:
                state[dep] = 1
                stack.append((dep, iter(dependencies(dep))))
    return tuple(ordered)
