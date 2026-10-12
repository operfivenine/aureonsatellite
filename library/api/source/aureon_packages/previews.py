"""Author previews, decoded directly to the cached display size."""
from pathlib import Path
import os, tempfile, logging
from PySide6.QtCore import QBuffer, QByteArray, QIODevice, Qt
from PySide6.QtGui import QImageReader
from .expressions import PackageError

def preview_path(revision):
    from aureon_preview_cache import PACKAGE_DIR
    return PACKAGE_DIR/(revision+'.png')

def persist_preview(raw, revision):
    buffer=QBuffer();buffer.setData(QByteArray(raw));buffer.open(QIODevice.OpenModeFlag.ReadOnly)
    reader=QImageReader(buffer);reader.setDecideFormatFromContent(True)
    size=reader.size()
    if bytes(reader.format()).lower()!=b'png' or size.width()<1 or size.height()<1:
        raise PackageError('Preview must be a valid PNG image')

    # PREVIEW01: source previews no longer have an artificial 1 MiB / 2048 px
    # restriction. Decode straight to the cache/display size so large source
    # images do not require a full-resolution QImage allocation first.
    target=size.scaled(640,360,Qt.KeepAspectRatio)
    reader.setScaledSize(target)
    image=reader.read()
    if image.isNull():raise PackageError('Cannot decode preview PNG')
    destination=preview_path(revision)
    temporary=None
    try:
        destination.parent.mkdir(parents=True,exist_ok=True)
        fd,temporary=tempfile.mkstemp(dir=destination.parent,suffix='.png');os.close(fd)
        if not image.save(temporary,'PNG'):raise OSError('Cannot save package preview')
        os.replace(temporary,destination);temporary=None
    except OSError:
        logging.getLogger('aureon').warning('Cannot persist package preview',exc_info=True)
    finally:
        if temporary:
            try:os.unlink(temporary)
            except OSError:pass
