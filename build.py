#!/usr/bin/env python3
"""Build / install helper for the Appear Offline WoT mod.

Run with your normal Python 3:

    python build.py            # compile + produce dist/<id>_<ver>.wotmod
    python build.py --dev      # also drop the .pyc into the game's res_mods (fast test loop)
    python build.py --install  # also copy the .wotmod into the game's mods/<version> folder

The mod source is compiled to .pyc with Python 2.7 (required by the game),
everything else is plain zipping done here in Python 3.
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
SRC = os.path.join(HERE, 'src', 'mod_appear_offline.py')
PYC = os.path.join(HERE, 'src', 'mod_appear_offline.pyc')
DIST = os.path.join(HERE, 'dist')
PYC_REL = 'scripts/client/gui/mods/mod_appear_offline.pyc'
SWF = os.path.join(HERE, 'as3', 'appear_offline_contacts_hook.swf')
SWF_REL = 'gui/flash/appear_offline_contacts_hook.swf'


def compile_pyc():
    if not os.path.exists(PYTHON27):
        sys.exit('Python 2.7 not found at %s - edit PYTHON27 in build.py' % PYTHON27)
    if os.path.exists(PYC):
        os.remove(PYC)
    # -m py_compile writes mod_appear_offline.pyc next to the source.
    subprocess.check_call([PYTHON27, '-m', 'py_compile', SRC])
    if not os.path.exists(PYC):
        sys.exit('Compilation failed: %s not produced' % PYC)
    print('compiled -> %s' % PYC)


def build_wotmod():
    os.makedirs(DIST, exist_ok=True)
    out = os.path.join(DIST, '%s_%s.wotmod' % (MOD_ID, VERSION))
    meta = (
        '<root>\n'
        '    <id>%s</id>\n'
        '    <version>%s</version>\n'
        '    <name>%s</name>\n'
        '    <description>%s</description>\n'
        '</root>' % (MOD_ID, VERSION, MOD_NAME, MOD_DESCRIPTION)
    )
    # .wotmod must be a STORED (uncompressed) zip.
    with zipfile.ZipFile(out, 'w', zipfile.ZIP_STORED) as z:
        z.writestr('meta.xml', meta)
        z.write(PYC, 'res/' + PYC_REL)
        if os.path.exists(SWF):
            z.write(SWF, 'res/' + SWF_REL)
        else:
            print('WARNING: %s missing - UI hook not packaged' % SWF)
    print('packaged -> %s' % out)
    return out


def dev_install():
    dst = os.path.join(GAME_DIR, 'res_mods', GAME_VERSION, *PYC_REL.split('/'))
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copyfile(PYC, dst)
    print('dev-installed -> %s' % dst)
    if os.path.exists(SWF):
        swf_dst = os.path.join(GAME_DIR, 'res_mods', GAME_VERSION, *SWF_REL.split('/'))
        os.makedirs(os.path.dirname(swf_dst), exist_ok=True)
        shutil.copyfile(SWF, swf_dst)
        print('dev-installed -> %s' % swf_dst)
    else:
        print('WARNING: %s missing - UI hook not dev-installed' % SWF)


def install_wotmod(wotmod_path):
    dst_dir = os.path.join(GAME_DIR, 'mods', GAME_VERSION)
    os.makedirs(dst_dir, exist_ok=True)
    dst = os.path.join(dst_dir, os.path.basename(wotmod_path))
    shutil.copyfile(wotmod_path, dst)
    print('installed -> %s' % dst)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dev', action='store_true',
                    help="copy the .pyc into the game's res_mods for a quick test")
    ap.add_argument('--install', action='store_true',
                    help="copy the built .wotmod into the game's mods/<version> folder")
    args = ap.parse_args()

    compile_pyc()
    wotmod = build_wotmod()
    if args.dev:
        dev_install()
    if args.install:
        install_wotmod(wotmod)
    print('done.')


if __name__ == '__main__':
    main()
