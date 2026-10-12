"""Build a theme ZIP. Run native validate_theme.py before importing the result."""
import argparse
import json
from pathlib import Path
import sys
import zipfile

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('folder',type=Path)
    parser.add_argument('output',type=Path)
    parser.add_argument('--overwrite',action='store_true')
    args=parser.parse_args()
    folder=args.folder.resolve();output=args.output.resolve()
    if args.folder.is_symlink() or not folder.is_dir():raise ValueError('Input must be a real directory')
    if output.is_relative_to(folder):raise ValueError('Output must be outside the input directory')
    if output.suffix.lower() not in ('.aurs','.aurp'):raise ValueError('Output extension must be .aurs or .aurp')
    if output.exists() and not args.overwrite:raise ValueError('Output exists; pass --overwrite to replace it')
    files=[]
    for path in sorted(folder.rglob('*')):
        if path.is_symlink() or path.is_junction():raise ValueError('Input links are not allowed: '+str(path))
        if path.is_dir():continue
        if not path.is_file():raise ValueError('Non-regular input file: '+str(path))
        rel=path.relative_to(folder).as_posix()
        if len(rel)>160 or ':' in rel or '\\' in rel:raise ValueError('Invalid package path: '+rel)
        files.append((path,rel))
    names=[rel for _,rel in files]
    if len(set(n.casefold() for n in names))!=len(names):raise ValueError('Case-insensitive path collision')
    entry='scene.json' if output.suffix.lower()=='.aurs' else 'projection.json'
    if not {'manifest.json',entry}<=set(names):raise ValueError('Missing root manifest/entry descriptor')
    output.parent.mkdir(parents=True,exist_ok=True)
    # This local tool creates only the user-selected package; it does not install it.
    with zipfile.ZipFile(output,'w' if args.overwrite else 'x',zipfile.ZIP_DEFLATED) as archive:
        for path,rel in files:archive.write(path,rel)
    with zipfile.ZipFile(output) as archive:
        if archive.testzip() is not None:raise ValueError('CRC verification failed')
    print(json.dumps({'status':'PACKED','path':str(output),'files':len(files),'native_validation_required':True}))

if __name__=='__main__':
    try:main()
    except (ValueError,OSError,zipfile.BadZipFile) as error:
        print(json.dumps({'status':'FAIL','error':str(error)}));sys.exit(1)
