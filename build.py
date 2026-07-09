# Copyright (c) 2026 Tosox

from __future__ import print_function

import argparse
import json
import os
import shutil
import subprocess
import sys
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, 'src')
BUILD = os.path.join(HERE, 'build')
PY_STAGE = os.path.join(BUILD, 'py_stage')
DIST = os.path.join(HERE, 'dist')
MOD_JSON = os.path.join(HERE, 'mod.json')
LOCAL_JSON = os.path.join(HERE, 'build.local.json')

ENTRY_RES_DIR = 'scripts/client/gui/mods'
PKG_RES_PARENT = 'scripts/client'

META_TEMPLATE = (
    '<root>\n'
    '    <id>{id}</id>\n'
    '    <version>{version}</version>\n'
    '    <name>{name}</name>\n'
    '    <description>{description}</description>\n'
    '</root>\n'
)


def load_mod():
    with open(MOD_JSON, 'r') as f:
        mod = json.load(f)
    mod.setdefault('prebuild', [])
    mod.setdefault('extra_files', [])
    return mod


def load_local():
    if os.path.exists(LOCAL_JSON):
        with open(LOCAL_JSON, 'r') as f:
            return json.load(f)
    return {}


def discover():
    entries = [n[:-3] for n in os.listdir(SRC)
               if n.startswith('mod_') and n.endswith('.py')]
    packages = [n for n in os.listdir(SRC)
                if os.path.isdir(os.path.join(SRC, n))]
    if len(entries) != 1:
        sys.exit('expected exactly one src/mod_*.py entry, found: %s' % entries)
    if len(packages) != 1:
        sys.exit('expected exactly one package dir under src/, found: %s' % packages)
    return entries[0], packages[0]


def find_python27():
    if sys.version_info[:2] == (2, 7):
        return sys.executable
    python27 = os.environ.get('PYTHON27')
    if not python27:
        sys.exit('Python 2.7 not set: $PYTHON27 (path to python.exe)')
    return python27


def run_prebuild(prebuild):
    for cmd in prebuild:
        print('prebuild: %s' % ' '.join(cmd))
        subprocess.check_call(cmd, cwd=HERE)


def compile_pyc():
    python27 = find_python27()
    if os.path.exists(PY_STAGE):
        shutil.rmtree(PY_STAGE)
    shutil.copytree(SRC, PY_STAGE,
                    ignore=shutil.ignore_patterns('*.pyc', '__pycache__'))
    subprocess.check_call([python27, '-m', 'compileall', '-q', PY_STAGE])
    print('compiled -> %s' % PY_STAGE)


def iter_payload(entry, package, extra_files):
    entry_pyc = os.path.join(PY_STAGE, entry + '.pyc')
    if not os.path.exists(entry_pyc):
        sys.exit('missing %s - compile step failed' % entry_pyc)
    yield entry_pyc, 'res/' + ENTRY_RES_DIR + '/' + entry + '.pyc'

    pkg_dir = os.path.join(PY_STAGE, package)
    for name in sorted(os.listdir(pkg_dir)):
        if name.endswith('.pyc'):
            yield (os.path.join(pkg_dir, name),
                   'res/' + PKG_RES_PARENT + '/' + package + '/' + name)

    for item in extra_files:
        src = os.path.join(HERE, item['src'])
        if os.path.exists(src):
            yield src, item['dst']
        else:
            print('WARNING: extra file missing, not packaged: %s' % item['src'])


def build_wotmod(mod, entry, package):
    if not os.path.isdir(DIST):
        os.makedirs(DIST)
    out = os.path.join(DIST, '%s_%s.wotmod' % (mod['id'], mod['version']))
    meta = META_TEMPLATE.format(id=mod['id'], version=mod['version'],
                                name=mod['name'], description=mod['description'])
    with zipfile.ZipFile(out, 'w', zipfile.ZIP_STORED) as z:
        z.writestr('meta.xml', meta)
        for src_path, archive_path in iter_payload(entry, package, mod['extra_files']):
            z.write(src_path, archive_path)
    print('packaged -> %s' % out)
    return out


def install_wotmod(wotmod_path, local):
    game_dir = local.get('game_dir')
    game_version = local.get('game_version')
    if not game_dir or not game_version:
        sys.exit('install needs "game_dir" and "game_version" in build.local.json')
    dst_dir = os.path.join(game_dir, 'mods', game_version)
    if not os.path.isdir(dst_dir):
        os.makedirs(dst_dir)
    dst = os.path.join(dst_dir, os.path.basename(wotmod_path))
    shutil.copyfile(wotmod_path, dst)
    print('installed -> %s' % dst)


def main():
    ap = argparse.ArgumentParser(description='Build a .wotmod from mod.json + src/.')
    ap.add_argument('--install', action='store_true',
                    help="copy the built .wotmod into the game's mods/<version> folder")
    args = ap.parse_args()

    mod = load_mod()
    local = load_local()
    entry, package = discover()
    run_prebuild(mod['prebuild'])
    compile_pyc()
    wotmod = build_wotmod(mod, entry, package)
    if args.install:
        install_wotmod(wotmod, local)
    print('done.')


if __name__ == '__main__':
    main()