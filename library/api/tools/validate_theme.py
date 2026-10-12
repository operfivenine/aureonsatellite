"""Prepare, without installing, a theme using the complete trusted Aureon host."""
import argparse
import hashlib
import json
import logging
import os
from pathlib import Path
import sys
import tempfile

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('package',type=Path)
    parser.add_argument('--host-source',required=True,type=Path)
    parser.add_argument('--allow-different-host',action='store_true')
    args=parser.parse_args()
    host=args.host_source.resolve()
    kit=Path(__file__).resolve().parent.parent
    baseline=json.loads((kit/'HOST_BASELINE.json').read_text(encoding='utf-8'))
    if not (host/'aureon_paths.py').is_file() or not (host/'aureon_packages/store.py').is_file():
        raise ValueError('--host-source must point to a complete trusted Aureon source tree, not the kit excerpt')
    differences=[]
    for row in baseline['reference_modules']:
        p=host/row['path']
        if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest()!=row['sha256']:
            differences.append(row['path'])
    if differences and not args.allow_different_host:
        raise ValueError('Host differs from the frozen reference in '+str(len(differences))+
                         ' files; first: '+differences[0]+'. Use the matching source or explicitly --allow-different-host.')
    sys.dont_write_bytecode=True
    sys.path.insert(0,str(host))
    # Keep the temporary profile inside the explicitly chosen working directory.
    # Some Windows sandbox temp mappings cannot remove their directory afterwards.
    with tempfile.TemporaryDirectory(prefix='.aureon-theme-validation-',dir=Path.cwd()) as temporary:
        isolated=Path(temporary)
        os.environ['AUREON_DATA_ROOT']=str(isolated)
        from PySide6.QtGui import QGuiApplication
        import aureon_preview_cache
        aureon_preview_cache.ROOT=isolated/'previews'
        aureon_preview_cache.PACKAGE_DIR=isolated/'previews/packages/v1'
        app=QGuiApplication([])
        from aureon_packages.store import prepare
        result=prepare(args.package.resolve(),'0.21.11')
        report={'status':'PASS','package':str(args.package.resolve()),'id':result.entry.id,
                'version':result.version,'renderer':result.entry.renderer,'native_prepare':True,
                'installed':False,'new_GL_run':False,'matching_reference_modules':not differences,
                'different_host_files':differences}
        del result
        app.quit()
        logging.shutdown()
    print(json.dumps(report,ensure_ascii=True))

if __name__=='__main__':
    try:main()
    except Exception as error:
        print(json.dumps({'status':'FAIL','error':str(error),'installed':False},ensure_ascii=True));sys.exit(1)
