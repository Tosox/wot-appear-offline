#!/usr/bin/env python3
"""Build / install helper for the Appear Offline WoT mod.

Run with your normal Python 3:

    python build.py            # compile + produce dist/<id>_<ver>.wotmod
    python build.py --install  # also copy the .wotmod into the game's mods/<version> folder

Layout: Python sources live in src/ (a thin entry module + the appear_offline
package); the compiled UI SWF is produced separately by src_flash/build_swf.sh
into build/. This script compiles the Python to .pyc with Python 2.7 (required
by the game), then zips everything into the res/ tree the game expects.

Nothing generated is ever written next to source: .pyc are compiled inside
build/py_stage/, and the .swf is read from build/.
"""
import argparse
import os
import shutil
import subprocess
import sys
import zipfile

# --- Configuration -----------------------------------------------------------
MOD_ID = 'de.tosox.appear_offline'
VERSION = '1.0.0'
MOD_NAME = 'Appear Offline'
MOD_DESCRIPTION = 'Appear offline to friends and clanmates while you keep playing'

PYTHON27 = r'C:\Python27\python.exe'
GAME_DIR = r'C:\Games\World_of_Tanks_EU'
GAME_VERSION = '2.3.0.1'  # res_mods/<version> and mods/<version> folder name

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, 'src')
BUILD = os.path.join(HERE, 'build')
PY_STAGE = os.path.join(BUILD, 'py_stage')
DIST = os.path.join(HERE, 'dist')
META_IN = os.path.join(HERE, 'meta.xml.in')
SWF = os.path.join(BUILD, 'appear_offline_contacts_hook.swf')

# Where sources map inside the game's res/ tree.
#   entry module   -> scripts/client/gui/mods/  (auto-loaded by WoT)
#   appear_offline -> scripts/client/           (top-level importable library)
#   UI hook SWF    -> gui/flash/
ENTRY_RES_DIR = 'scripts/client/gui/mods'
PKG_RES_DIR = 'scripts/client/appear_offline'
SWF_REL = 'gui/flash/appear_offline_contacts_hook.swf'


def compile_pyc():
    """Compile every .py in src/ to .pyc inside build/py_stage (never in src/)."""
    if not os.path.exists(PYTHON27):
        sys.exit('Python 2.7 not found at %s - edit PYTHON27 in build.py' % PYTHON27)
    if os.path.exists(PY_STAGE):
        shutil.rmtree(PY_STAGE)
    shutil.copytree(SRC, PY_STAGE,
                    ignore=shutil.ignore_patterns('*.pyc', '__pycache__'))
    subprocess.check_call([PYTHON27, '-m', 'compileall', '-q', PY_STAGE])
    print('compiled -> %s' % PY_STAGE)


def iter_payload():
    """Yield (abs_source_path, res_relative_path) for every file that goes into
    the mod: the entry .pyc, each package .pyc, and the UI SWF."""
    entry = os.path.join(PY_STAGE, 'mod_appear_offline.pyc')
    if not os.path.exists(entry):
        sys.exit('missing %s - compile step failed' % entry)
    yield entry, ENTRY_RES_DIR + '/mod_appear_offline.pyc'

    pkg = os.path.join(PY_STAGE, 'appear_offline')
    for name in sorted(os.listdir(pkg)):
        if name.endswith('.pyc'):
            yield os.path.join(pkg, name), PKG_RES_DIR + '/' + name

    if os.path.exists(SWF):
        yield SWF, SWF_REL
    else:
        print('WARNING: %s missing - UI hook not packaged (run src_flash/build_swf.sh)' % SWF)


def render_meta():
    with open(META_IN, 'r') as f:
        template = f.read()
    return template.format(id=MOD_ID, version=VERSION,
                           name=MOD_NAME, description=MOD_DESCRIPTION)


def build_wotmod():
    os.makedirs(DIST, exist_ok=True)
    out = os.path.join(DIST, '%s_%s.wotmod' % (MOD_ID, VERSION))
    # .wotmod must be a STORED (uncompressed) zip.
    with zipfile.ZipFile(out, 'w', zipfile.ZIP_STORED) as z:
        z.writestr('meta.xml', render_meta())
        for src_path, res_rel in iter_payload():
            z.write(src_path, 'res/' + res_rel)
    print('packaged -> %s' % out)
    return out


def install_wotmod(wotmod_path):
    dst_dir = os.path.join(GAME_DIR, 'mods', GAME_VERSION)
    os.makedirs(dst_dir, exist_ok=True)
    dst = os.path.join(dst_dir, os.path.basename(wotmod_path))
    shutil.copyfile(wotmod_path, dst)
    print('installed -> %s' % dst)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--install', action='store_true',
                    help="copy the built .wotmod into the game's mods/<version> folder")
    args = ap.parse_args()

    compile_pyc()
    wotmod = build_wotmod()
    if args.install:
        install_wotmod(wotmod)
    print('done.')


if __name__ == '__main__':
    main()
