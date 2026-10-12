"""One ordered catalog for selectors, validation and trusted runtime factories."""
import logging


class ContentRegistry:
    def __init__(self):
        self._entries = {}
        self._aliases = {}
        self._listeners = []
        self.generation = 0

    def add_builtin(self, entry):
        if entry.source != 'builtin':
            raise ValueError('External content requires the future package installer')
        if entry.kind not in ('scene', 'projection') or not entry.id:
            raise ValueError('Invalid content descriptor')
        names = (entry.id,) + ((entry.reactive_id,) if entry.reactive_id else ())
        if len(set(names)) != len(names) or any(n in self._entries or n in self._aliases for n in names):
            raise ValueError('Duplicate content identity')
        self._entries[entry.id] = entry
        if entry.reactive_id:
            self._aliases[entry.reactive_id] = entry.id
        self.generation += 1
        self._notify()

    def validate_package(self, entry):
        profiles = {'projection': ('projection.canvas.v1','projection.surface.experimental.v2'),
                    'scene': ('scene.fullscreen_frag.v1','scene.fullscreen_frag.v2','scene.mesh.experimental.v1','scene.hybrid_mesh.experimental.v1')}
        if entry.source != 'package' or entry.renderer not in profiles.get(entry.kind, ()) or entry.factory is None:
            raise ValueError('Unsupported external content descriptor')
        existing = self.resolve(entry.id)
        if existing is not None and (existing.source != 'package' or existing.kind != entry.kind or existing.id != entry.id):
            raise ValueError('Content identity is already in use')
        if entry.reactive_id:
            alias = self.resolve(entry.reactive_id)
            if alias is not None and alias.id != entry.id:
                raise ValueError('Reactive identity is already in use')

    def add_package(self, entry):
        self.validate_package(entry)
        previous = self._entries.get(entry.id)
        if previous is not None and previous.reactive_id:
            self._aliases.pop(previous.reactive_id, None)
        self._entries[entry.id] = entry
        if entry.reactive_id:
            self._aliases[entry.reactive_id] = entry.id
        self.generation += 1
        self._notify()

    def remove_package(self, key, kind=None):
        """Remove one external content entry and publish a catalog refresh.

        Built-ins are deliberately immutable through this API.  PackageStore
        owns filesystem mutation; the registry only removes the validated
        catalog entry/alias after the package blob has been deleted.
        """
        entry = self.resolve(key, kind)
        if entry is None:
            raise KeyError(str(key))
        if entry.source != 'package':
            raise ValueError('Built-in content cannot be removed')
        self._entries.pop(entry.id, None)
        if entry.reactive_id:
            self._aliases.pop(entry.reactive_id, None)
        self.generation += 1
        self._notify()
        return entry

    def resolve(self, key, kind=None):
        entry = self._entries.get(self._aliases.get(str(key), str(key)))
        return entry if entry is not None and (kind is None or entry.kind == kind) else None

    def entries(self, kind):
        return tuple(e for e in self._entries.values() if e.kind == kind)

    def keys(self, kind):
        return tuple(e.id for e in self.entries(kind))

    def items(self, kind):
        return tuple((e.name, e.id) for e in self.entries(kind))

    def reactive_map(self):
        return {e.id: e.reactive_id for e in self.entries('scene') if e.reactive_id}

    def is_gl(self, key):
        entry = self.resolve(key, 'scene')
        return entry is not None and entry.renderer in ('builtin.gl', 'scene.fullscreen_frag.v1', 'scene.fullscreen_frag.v2', 'scene.mesh.experimental.v1', 'scene.hybrid_mesh.experimental.v1')

    def supports_extreme(self, key):
        entry = self.resolve(key, 'scene')
        return entry is not None and entry.supports_extreme

    def localized_items(self, kind, language):
        from aureon_i18n import tr
        result = []
        for entry in self.entries(kind):
            names = dict(entry.names)
            label = names.get(language, names.get('en', entry.name))
            if entry.label_key: label = tr(entry.label_key, language)
            result.append((entry.name if label == entry.label_key else label, entry.id))
        return tuple(result)

    def subscribe(self, listener):
        if listener not in self._listeners:
            self._listeners.append(listener)

    def unsubscribe(self, listener):
        if listener in self._listeners:
            self._listeners.remove(listener)

    def _notify(self):
        for listener in tuple(self._listeners):
            try:
                listener(self.generation)
            except Exception:
                logging.getLogger('aureon').exception('Content catalog refresh failed')
