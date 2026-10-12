"""Seed official projections once; update only byte-identical original packages."""
import json
import logging
from hashlib import sha256

from aureon_paths import resource_path
from aureon_packages.store import atomic_write


def install_bundled_projections(store):
    directory = resource_path('assets', 'projections')
    marker = store.root / '.bundled-projections.json'
    try:
        catalog = json.loads((directory / 'catalog.json').read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return
    try:
        raw = marker.read_bytes()
        seen = json.loads(raw) if len(raw) <= 65536 else {}
        if not isinstance(seen, dict):
            seen = {}
    except (OSError, ValueError):
        seen = {}
    updated = dict(seen)
    for content_id, item in catalog.items():
        try:
            package = directory / item['filename']
            revision = sha256(package.read_bytes()).hexdigest()
            installed = store.root / (content_id + '.aurp')
            if installed.is_file():
                # Preserve user variants and future imports. The installer
                # retains the original v1/v2 package in the store's previous/.
                previous = item['previous_sha256']
                previous = previous if isinstance(previous, list) else [previous]
                if sha256(installed.read_bytes()).hexdigest() in previous:
                    store.install(package)
            elif content_id not in seen:
                store.install(package)
            # A later explicit uninstall remains uninstalled on startup.
            updated[content_id] = revision
        except Exception:
            logging.getLogger('aureon').exception('Could not seed projection %s', content_id)
    if updated != seen:
        try:
            atomic_write(marker, (json.dumps(updated, indent=2) + '\n').encode('utf-8'))
        except OSError:
            logging.getLogger('aureon').warning('Could not save bundled projection marker')
