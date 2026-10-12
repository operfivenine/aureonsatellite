"""Read bounded ZIP packages without extraction; persist only validated blobs."""
from .limits import LIMITS

from dataclasses import dataclass
from hashlib import sha256
from io import BytesIO
import json
import logging
import os
from pathlib import Path, PurePosixPath
import stat
import tempfile
import threading
import time
from zipfile import ZipFile, BadZipFile, ZIP_STORED, ZIP_DEFLATED

from aureon_content.models import ContentEntry
from .expressions import PackageError
from .schema import manifest, projection, HOLOGRAM_FEATURE, LIGHT_FEATURE
from .aurp_standard_library import AURP_STANDARD_LIBRARY_FEATURE

MAX_ARCHIVE = LIMITS["archive_bytes"]
MAX_EXPANDED = LIMITS["expanded_bytes"]


def json_object(raw):
    if len(raw) > LIMITS["json_bytes"]: raise PackageError('JSON resource is too large')
    def unique(pairs):
        out = {}
        for key, value in pairs:
            if key in out: raise PackageError('Duplicate JSON field: '+key)
            out[key] = value
        return out
    def invalid(value): raise PackageError('Invalid JSON number: '+value)
    try:
        return json.loads(raw.decode('utf-8-sig'), object_pairs_hook=unique, parse_constant=invalid)
    except (UnicodeError, ValueError, RecursionError) as exc:
        raise PackageError('Invalid JSON: '+str(exc)[:180]) from exc


@dataclass(frozen=True)
class PreparedPackage:
    data: bytes
    entry: ContentEntry
    version: str


def prepare(path, app_version):
    path = Path(path)
    suffix = path.suffix.lower()
    if suffix not in ('.aurp', '.aurs'):
        raise PackageError('Select an .aurp or .aurs package')
    kind = 'scene' if suffix == '.aurs' else 'projection'
    entry_file = 'scene.json' if kind == 'scene' else 'projection.json'
    try:
        with path.open('rb') as f:
            blob = f.read(MAX_ARCHIVE+1)
        if len(blob) > MAX_ARCHIVE: raise PackageError('Package exceeds 800 MiB')
        files, total, seen = {}, 0, set()
        with ZipFile(BytesIO(blob)) as archive:
            if len(archive.infolist()) > LIMITS["archive_entries"]: raise PackageError('Too many archive entries')
            for item in archive.infolist():
                name = item.filename
                trimmed = name[:-1] if item.is_dir() else name
                parts = PurePosixPath(trimmed).parts
                if (not trimmed or len(name) > 160 or '\\' in name or ':' in name or '\x00' in name
                    or name.startswith('/') or any(x in ('', '.', '..') for x in trimmed.split('/'))
                    or trimmed.casefold() in seen):
                    raise PackageError('Invalid or duplicate archive path')
                seen.add(trimmed.casefold())
                mode = item.external_attr >> 16
                if stat.S_ISLNK(mode) or stat.S_IFMT(mode) not in (0, stat.S_IFREG, stat.S_IFDIR):
                    raise PackageError('Archive links and special files are forbidden')
                if item.is_dir():
                    expected_dir = 'shaders' if kind == 'scene' else 'assets'
                    if trimmed not in ((expected_dir, 'textures', 'meshes') if kind == 'scene' else (expected_dir,)): raise PackageError('Unsupported archive directory')
                    continue
                if item.flag_bits & 1 or item.compress_type not in (ZIP_STORED, ZIP_DEFLATED):
                    raise PackageError('Unsupported archive compression/encryption')
                allowed = name in ('manifest.json', entry_file)
                if kind == 'scene':
                    allowed = allowed or name in ('shaders/main.frag', 'shaders/main.vert', 'shaders/background.frag', 'preview.png') or (len(parts)==2 and parts[0]=='meshes' and parts[1] in ('low.bin','medium.bin','high.bin')) or (len(parts) == 2 and parts[0] == 'textures' and parts[1].endswith(('.png','.jpg','.jpeg')))
                else:
                    allowed = allowed or (len(parts) == 2 and parts[0] == 'assets' and parts[1].endswith('.png'))
                if not allowed: raise PackageError('Unsupported package resource: '+name)
                total += item.file_size
                if kind == 'scene' and ((name.startswith('meshes/') and item.file_size > 80_000_000) or (name == 'shaders/main.vert' and item.file_size > 128*1024)):
                    raise PackageError('Mesh profile resource limit exceeded')
                if item.file_size > LIMITS["resource_bytes"] or total > MAX_EXPANDED:
                    raise PackageError('Expanded package limit exceeded')
                with archive.open(item) as source:
                    raw = source.read(min(item.file_size, LIMITS["resource_bytes"])+1)
                if len(raw) != item.file_size: raise PackageError('Invalid archive entry length')
                files[name] = raw
        if 'manifest.json' not in files or entry_file not in files:
            raise PackageError('manifest.json and '+entry_file+' are required at package root')
        metadata = manifest(json_object(files['manifest.json']), app_version, kind)
        has_preview = 'preview' in metadata
        if kind == 'scene' and (('preview.png' in files) != has_preview):
            raise PackageError('preview.png and manifest.preview must be provided together')
        if has_preview and 'scene.preview.v1' not in metadata.get('features',{}).get('required',[]):
            raise PackageError('Preview requires scene.preview.v1')
        if kind == 'scene':
            if metadata['renderer'] in ('scene.mesh.experimental.v1', 'scene.hybrid_mesh.experimental.v1'):
                from aureon_geometry.schema import compile_scene
                definition = compile_scene(json_object(files[entry_file]), files, hybrid=metadata['renderer']=='scene.hybrid_mesh.experimental.v1',features=metadata['features']['required'])
                def factory(quality, reactive):
                    from aureon_geometry.runtime import MeshRuntime
                    return MeshRuntime(definition, quality, reactive)
                reactive_id = metadata['id']+'__reactive'
            else:
                if any(k.startswith('meshes/') or k.endswith('.vert') or k=='shaders/background.frag' for k in files): raise PackageError('Mesh resources require the mesh renderer')
                from .scene_schema import scene
                from .scene_runtime import PackageSceneRuntime
                profile = 2 if metadata['renderer'] == 'scene.fullscreen_frag.v2' else 1
                scene_data = json_object(files[entry_file])
                if not isinstance(scene_data, dict): raise PackageError('scene.json must be an object')
                if scene_data.get('textures') and 'scene.textures2d.experimental.v1' not in metadata.get('features', {}).get('required', []):
                    raise PackageError('Textures require scene.textures2d.experimental.v1')
                if profile != 2 and any(k.startswith('textures/') for k in files):
                    raise PackageError('Textures require scene.fullscreen_frag.v2')
                if 'lights' in scene_data and (profile != 2 or 'scene.lights_config.experimental.v1' not in metadata.get('features', {}).get('required', [])):
                    raise PackageError('lights requires AURS v2 and scene.lights_config.experimental.v1')
                if 'extreme' in scene_data.get('quality', {}) and 'scene.quality_extreme.experimental.v1' not in metadata.get('features',{}).get('required',[]):
                    raise PackageError('Extreme requires scene.quality_extreme.experimental.v1')
                camera_data=scene_data.get('behavior',{}).get('camera') if isinstance(scene_data.get('behavior',{}),dict) else None
                if isinstance(camera_data,dict) and 'presets' in camera_data and (profile != 2 or 'scene.camera_presets.experimental.v1' not in metadata.get('features',{}).get('required',[])):
                    raise PackageError('Camera presets require scene.camera_presets.experimental.v1')
                if isinstance(camera_data,dict) and 'manual' in camera_data and (profile != 2 or 'scene.camera_manual.experimental.v1' not in metadata.get('features',{}).get('required',[])):
                    raise PackageError('Manual camera requires scene.camera_manual.experimental.v1')
                definition = scene(scene_data, files, profile)
                if profile == 2:
                    from .scene_v2_runtime import PackageSceneRuntimeV2
                runtime_type = PackageSceneRuntimeV2 if profile == 2 else PackageSceneRuntime
                def factory(quality, reactive):
                    return runtime_type(definition, quality, reactive)
                reactive_id = metadata['id']+'__reactive'
        elif metadata['renderer'] == 'projection.surface.experimental.v2':
            from .projection_surface import projection_surface, FEATURE, SPECTRUM_FEATURE
            required = set(metadata.get('features', {}).get('required', []))
            if not {FEATURE, SPECTRUM_FEATURE} <= required:
                raise PackageError('GPU surface requires its renderer and spectrum64 features')
            if set(files) != {'manifest.json','projection.json'}:
                raise PackageError('GPU surface packages contain only manifest.json and projection.json')
            definition = projection_surface(json_object(files[entry_file]))
            if definition.model == 'gyro_rings':
                from .projection_surface import GYRO_FEATURE
                if GYRO_FEATURE not in required:
                    raise PackageError('Gyro Rings requires '+GYRO_FEATURE)
            from projection.surface import SurfaceProjectionWindow
            def factory(frame_provider):
                return SurfaceProjectionWindow(frame_provider, definition)
            reactive_id = ''
        else:
            assets = {k:v for k,v in files.items() if k.startswith('assets/')}
            projection_data = json_object(files[entry_file])
            if not isinstance(projection_data, dict):
                raise PackageError('projection.json must be an object')
            requested_aurp_libraries = projection_data.get('libraries', [])
            if requested_aurp_libraries and AURP_STANDARD_LIBRARY_FEATURE not in metadata.get('features', {}).get('required', []):
                raise PackageError('AURP libraries require '+AURP_STANDARD_LIBRARY_FEATURE)
            definition = projection(projection_data, assets)
            required = metadata.get('features', {}).get('required', [])
            def has_hologram(nodes):
                return any(n['type']=='hologram' or (n['type']=='group' and has_hologram(n['nodes'])) for n in nodes)
            if has_hologram(definition.nodes) and HOLOGRAM_FEATURE not in required:
                raise PackageError('Hologram nodes require '+HOLOGRAM_FEATURE)
            if (definition.supersample != 1 or definition.bloom > 0) and LIGHT_FEATURE not in required:
                raise PackageError('Light canvas requires '+LIGHT_FEATURE)
            from projection.declarative import decode_images, DeclarativeProjectionWindow
            images = decode_images(assets)
            def factory(frame_provider):
                return DeclarativeProjectionWindow(frame_provider, definition, images)
            reactive_id = ''

        def public_name(value):
            value = str(value).strip()
            if value.startswith('AURP · '):
                cleaned = value[7:].strip()
                return cleaned or value
            if value.startswith('AURS · '):
                cleaned = value[7:].strip()
                return cleaned or value
            return value

        public_names = {lang: public_name(value) for lang, value in metadata['name'].items()}
        # OPT 06.2: scene packages are immutable by revision and can safely use
        # Qt's cacheable shader path.  QOpenGLShaderProgram derives its cache key
        # from the shader sources/context; a changed .aurs therefore cannot reuse
        # the stale linked binary.  Projection packages do not create this GL path.
        entry = ContentEntry(metadata['id'], kind, public_names['en'], metadata['renderer'],
                             reactive_id=reactive_id, factory=factory, source='package',
                             revision=sha256(blob).hexdigest(), names=tuple(public_names.items()),
                             shader_cache=(kind == 'scene'),
                             camera_presets=tuple((getattr(definition,'behavior',{}).get('camera') or {}).get('presets',())) if kind=='scene' else (),
                             supports_extreme=(kind == 'scene' and 'extreme' in definition.quality))
        if has_preview:
            from .previews import persist_preview
            persist_preview(files['preview.png'],entry.revision)
        return PreparedPackage(blob, entry, metadata['version'])
    except PackageError:
        raise
    except (OSError, BadZipFile, RuntimeError, ValueError, TypeError, KeyError, OverflowError, RecursionError) as exc:
        raise PackageError('Cannot read package: '+str(exc)[:180]) from exc


def atomic_write(path, blob):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, prefix='.import-', suffix='.tmp', delete=False) as f:
            temporary = Path(f.name)
            f.write(blob)
            f.flush()
            os.fsync(f.fileno())
        os.replace(temporary, path)
    finally:
        if temporary is not None and temporary.exists(): temporary.unlink()


# OPT 06.3: persistent validated catalog cache.  The cache contains metadata
# only (never executable/pickled objects).  An unchanged package can therefore
# be published into the content registry without repeating ZIP/schema work on
# the GUI thread.  The full validated factory is prepared lazily on first use
# and memoized for the rest of the process.
PACKAGE_CACHE_FORMAT = 1
PACKAGE_PREPARE_CONTRACT = 'hybrid05-planar-materials-aurs-api1.1-camera-ui04-aurp-hologram-light01-quality-capabilities01-limits100x-WIN12-FIX10-GYRO01'
PACKAGE_CACHE_NAME = '.aureon_prepared_catalog_v1.json'


def _stat_signature(path):
    st = path.stat()
    return {
        'size': int(st.st_size),
        'mtime_ns': int(st.st_mtime_ns),
        'ctime_ns': int(getattr(st, 'st_ctime_ns', int(st.st_ctime * 1_000_000_000))),
    }


def _cache_record(package, path):
    entry = package.entry
    signature = _stat_signature(path)
    return {
        **signature,
        'id': entry.id,
        'kind': entry.kind,
        'name': entry.name,
        'renderer': entry.renderer,
        'reactive_id': entry.reactive_id,
        'revision': entry.revision,
        'version': package.version,
        'names': [[str(k), str(v)] for k, v in entry.names],
        'shader_cache': bool(entry.shader_cache),
        'camera_presets': [list(p) for p in entry.camera_presets],
        'supports_extreme': bool(entry.supports_extreme),
        'has_preview': __import__('aureon_packages.previews',fromlist=['preview_path']).preview_path(entry.revision).is_file(),
    }


def _record_matches(record, path, kind):
    if not isinstance(record, dict):
        return False
    try:
        signature = _stat_signature(path)
    except OSError:
        return False
    if any(record.get(key) != value for key, value in signature.items()):
        return False
    if record.get('kind') != kind or record.get('id') != path.stem:
        return False
    renderer = record.get('renderer')
    if renderer in ('scene.mesh.experimental.v1', 'scene.hybrid_mesh.experimental.v1'):
        from aureon_geometry import enabled
        if not enabled(): return False
    if kind == 'scene':
        if renderer not in ('scene.fullscreen_frag.v1', 'scene.fullscreen_frag.v2', 'scene.mesh.experimental.v1', 'scene.hybrid_mesh.experimental.v1'):
            return False
    elif renderer not in ('projection.canvas.v1','projection.surface.experimental.v2'):
        return False
    if not isinstance(record.get('name'), str) or not record['name']:
        return False
    if not isinstance(record.get('revision'), str) or len(record['revision']) != 64:
        return False
    if record.get('has_preview', False):
        from .previews import preview_path
        if not preview_path(record['revision']).is_file():return False
    reactive_id = record.get('reactive_id', '')
    if not isinstance(reactive_id, str):
        return False
    presets=record.get('camera_presets',[])
    if not isinstance(presets,list) or len(presets)>LIMITS["camera_presets"]:return False
    seen=set()
    for p in presets:
        if not isinstance(p,list) or len(p)!=4:return False
        if any(not isinstance(v,str) or not v or len(v)>48 for v in p[:3]):return False
        if p[0]=='auto' or p[0] in seen or type(p[3]) is not int or not 0<=p[3]<LIMITS["camera_shots"]:return False
        seen.add(p[0])
    names = record.get('names')
    if not isinstance(names, list) or not names:
        return False
    for item in names:
        if not isinstance(item, list) or len(item) != 2 or not all(isinstance(x, str) for x in item):
            return False
    if type(record.get('shader_cache')) is not bool:
        return False
    if type(record.get('supports_extreme')) is not bool:
        return False
    return True


def _lazy_cached_entry(path, app_version, record):
    """Recreate a safe registry descriptor from validated cache metadata.

    The cache itself never provides runtime code.  On first activation we run
    the normal package validator again, verify the previously accepted revision,
    then memoize only the trusted in-memory factory returned by ``prepare``.
    """
    path = Path(path)
    logger = logging.getLogger('aureon')
    state = {'factory': None}
    lock = threading.Lock()

    def resolved_factory():
        factory = state['factory']
        if factory is not None:
            return factory
        with lock:
            factory = state['factory']
            if factory is not None:
                return factory
            started = time.perf_counter()
            package = prepare(path, app_version)
            if package.entry.id != record['id'] or package.entry.kind != record['kind']:
                raise PackageError('Cached package identity changed; restart Aureon')
            if package.entry.revision != record['revision']:
                raise PackageError('Cached package changed after startup; restart Aureon')
            factory = package.entry.factory
            state['factory'] = factory
            logger.info('[AURS LOAD] package.lazy_prepare kind=%s file=%s ms=%.3f',
                        record['kind'], path.name, (time.perf_counter()-started)*1000.0)
            return factory

    def factory(*args, **kwargs):
        return resolved_factory()(*args, **kwargs)

    names = tuple((str(item[0]), str(item[1])) for item in record['names'])
    return ContentEntry(
        id=record['id'], kind=record['kind'], name=record['name'], renderer=record['renderer'],
        reactive_id=record.get('reactive_id', ''), factory=factory, source='package',
        revision=record['revision'], names=names, shader_cache=bool(record.get('shader_cache', False)),
        camera_presets=tuple(tuple(p) for p in record.get('camera_presets',[])),
        supports_extreme=record['supports_extreme'])


class PackageStore:
    def __init__(self, root, registry, app_version, kind='projection'):
        if kind not in ('projection', 'scene'):
            raise ValueError('Unsupported package store kind')
        self.kind = kind
        self.extension = '.aurs' if kind == 'scene' else '.aurp'
        self.root = Path(root)
        self.registry = registry
        self.app_version = app_version
        self.failures = []

    def _cache_path(self):
        return self.root / PACKAGE_CACHE_NAME

    def _load_cache(self):
        try:
            raw = self._cache_path().read_bytes()
            if len(raw) > LIMITS["json_bytes"]:
                return {}
            payload = json.loads(raw.decode('utf-8'))
            if (not isinstance(payload, dict) or payload.get('format') != PACKAGE_CACHE_FORMAT
                or payload.get('prepare_contract') != PACKAGE_PREPARE_CONTRACT
                or payload.get('app_version') != self.app_version or payload.get('kind') != self.kind
                or not isinstance(payload.get('entries'), dict)):
                return {}
            return payload['entries']
        except (OSError, UnicodeError, ValueError, TypeError):
            return {}

    def _save_cache(self, entries):
        try:
            self.root.mkdir(parents=True, exist_ok=True)
            payload = {
                'format': PACKAGE_CACHE_FORMAT,
                'prepare_contract': PACKAGE_PREPARE_CONTRACT,
                'app_version': self.app_version,
                'kind': self.kind,
                'entries': entries,
            }
            raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')
            atomic_write(self._cache_path(), raw)
        except OSError:
            logging.getLogger('aureon').warning('Could not persist %s package catalog cache', self.kind)

    def scan(self):
        if not self.root.is_dir():
            return
        logger = logging.getLogger('aureon')
        scan_started = time.perf_counter()
        paths = sorted(self.root.glob('*'+self.extension))
        cached = self._load_cache()
        updated = {}
        loaded = 0
        failed = 0
        hits = 0
        misses = 0
        for path in paths:
            package_started = time.perf_counter()
            record = cached.get(path.name)
            try:
                if _record_matches(record, path, self.kind):
                    entry = _lazy_cached_entry(path, self.app_version, record)
                    self.registry.add_package(entry)
                    updated[path.name] = record
                    loaded += 1
                    hits += 1
                    logger.info('[AURS LOAD] package.cache_hit kind=%s file=%s ms=%.3f bytes=%d',
                                self.kind, path.name, (time.perf_counter()-package_started)*1000.0,
                                int(record['size']))
                    continue

                misses += 1
                package = prepare(path, self.app_version)
                if package.entry.kind != self.kind: raise PackageError('Package type mismatch')
                if path.stem != package.entry.id: raise PackageError('Installed package ID does not match filename')
                self.registry.add_package(package.entry)
                updated[path.name] = _cache_record(package, path)
                loaded += 1
                logger.info('[AURS LOAD] package.prepare kind=%s file=%s cache=miss ms=%.3f bytes=%d',
                            self.kind, path.name, (time.perf_counter()-package_started)*1000.0,
                            updated[path.name]['size'])
            except Exception as exc:
                failed += 1
                self.failures.append((path.name, str(exc)))
                logger.warning('Skipped %s package %s: %s', self.kind, path.name, exc)
        if updated != cached:
            self._save_cache(updated)
        logger.info('[AURS LOAD] package.scan kind=%s files=%d loaded=%d failed=%d hits=%d misses=%d total_ms=%.3f',
                    self.kind, len(paths), loaded, failed, hits, misses,
                    (time.perf_counter()-scan_started)*1000.0)

    def install(self, path):
        install_started = time.perf_counter()
        prepare_started = install_started
        package = prepare(path, self.app_version)
        prepare_ms = (time.perf_counter()-prepare_started)*1000.0
        entry = package.entry
        if entry.kind != self.kind: raise PackageError('Package type mismatch')
        current = self.registry.resolve(entry.id)
        if current is not None and (current.source != 'package' or current.kind != entry.kind or current.id != entry.id):
            raise PackageError('A package cannot replace built-in content')
        if current is not None and current.revision == entry.revision:
            return current
        self.registry.validate_package(entry)
        destination = self.root / (entry.id+self.extension)
        previous = destination.read_bytes() if destination.exists() else None
        if previous is not None:
            atomic_write(self.root/'previous'/(entry.id+self.extension), previous)
        atomic_write(destination, package.data)
        try:
            self.registry.add_package(entry)
        except Exception:
            if previous is None: destination.unlink(missing_ok=True)
            else: atomic_write(destination, previous)
            raise
        cached = self._load_cache()
        cached[destination.name] = _cache_record(package, destination)
        self._save_cache(cached)
        logging.getLogger('aureon').info(
            '[AURS LOAD] package.install kind=%s id=%s prepare_ms=%.3f total_ms=%.3f bytes=%d',
            self.kind, entry.id, prepare_ms, (time.perf_counter()-install_started)*1000.0, len(package.data))
        return entry

    def uninstall(self, content_id):
        """Remove one installed package of this store kind.

        Only registry entries whose source is ``package`` are eligible.  The
        active blob is removed first; if publishing the catalog change fails,
        the blob is restored so disk and registry cannot silently diverge.
        """
        content_id = str(content_id or '').strip()
        entry = self.registry.resolve(content_id, self.kind)
        if entry is None:
            raise PackageError('Installed package was not found')
        if entry.source != 'package':
            raise PackageError('Built-in content cannot be removed')

        destination = self.root / (entry.id + self.extension)
        if not destination.is_file():
            raise PackageError('Installed package file was not found')
        try:
            previous_blob = destination.read_bytes()
            destination.unlink()
        except OSError as exc:
            raise PackageError('Cannot remove installed package: '+str(exc)[:180]) from exc

        try:
            removed = self.registry.remove_package(entry.id, self.kind)
        except Exception:
            try:
                atomic_write(destination, previous_blob)
            except Exception:
                logging.getLogger('aureon').exception('Failed to restore package after uninstall rollback: %s', destination)
            raise

        # Old replacement snapshots are not installed/scanned.  Remove them
        # opportunistically so deleting a package also clears its stale copy.
        try:
            (self.root/'previous'/(entry.id+self.extension)).unlink(missing_ok=True)
        except OSError:
            logging.getLogger('aureon').warning('Could not remove previous %s package snapshot: %s', self.kind, entry.id)
        cached = self._load_cache()
        if cached.pop(destination.name, None) is not None:
            self._save_cache(cached)
        return removed

