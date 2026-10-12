"""Shared scene resolution policy; content/chrome always use native resolution."""

def background_size(width, height, quality='auto', fixed=None, limit=None, resolution=None):
    width, height = max(1, int(width)), max(1, int(height))
    if fixed:
        width, height = max(1, int(fixed[0])), max(1, int(fixed[1]))
    scale = 1.0
    if quality == 'lowest':
        scale = min(.5, 960 / width, 540 / height)
    if resolution in (25, 50, 75, 100):
        scale = resolution / 100.0
    if limit and not fixed:
        scale = min(scale, max(1, limit[0]) / width, max(1, limit[1]) / height)
    return max(1, round(width * scale)), max(1, round(height * scale))
