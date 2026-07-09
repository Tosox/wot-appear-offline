from __future__ import print_function

import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
MOD_JSON = os.path.join(ROOT, 'mod.json')

TARGET_PLAYER = '11.1'
SWF_VERSION = 17


def flex_cmd(flex, tool, args):
    launcher = os.path.join(flex, 'bin', tool)
    if os.name == 'nt':
        return ['cmd', '/c', launcher + '.bat'] + args
    return [launcher] + args


def main():
    flex = os.environ.get('FLEX_HOME')
    if not flex:
        sys.exit('$FLEX_HOME not set (path to the Flex SDK)')
    flex = os.path.abspath(flex)
    if not os.path.isdir(os.path.join(flex, 'bin')):
        sys.exit('Flex SDK not found at %s' % flex)

    with open(MOD_JSON, 'r') as f:
        flash = json.load(f).get('flash')
    if not flash:
        sys.exit('no "flash" block in mod.json')

    playerglobal_home = os.path.join(flex, 'frameworks', 'libs', 'player')
    playerglobal = os.path.join(playerglobal_home, TARGET_PLAYER, 'playerglobal.swc')
    if not os.path.exists(playerglobal):
        sys.exit('playerglobal.swc missing at %s' % playerglobal)

    main_as = os.path.join(ROOT, flash['main'])
    stubs = os.path.join(ROOT, flash['stubs'])
    output = os.path.join(ROOT, flash['output'])
    stub_swc = os.path.join(ROOT, flash['stub_swc'])

    out_dir = os.path.dirname(output)
    if not os.path.isdir(out_dir):
        os.makedirs(out_dir)

    env = dict(os.environ)
    env['PLAYERGLOBAL_HOME'] = playerglobal_home

    print('[1/2] compc: external stub swc')
    subprocess.check_call(flex_cmd(flex, 'compc', [
        '-source-path', stubs, '-include-sources', stubs,
        '-target-player=' + TARGET_PLAYER, '-output', stub_swc,
    ]), env=env)

    print('[2/2] mxmlc: hook swf')
    subprocess.check_call(flex_cmd(flex, 'mxmlc', [
        main_as,
        '-source-path=' + os.path.dirname(main_as),
        '-external-library-path+=' + stub_swc,
        '-static-link-runtime-shared-libraries=true',
        '-target-player=' + TARGET_PLAYER,
        '-swf-version=' + str(SWF_VERSION),
        '-output', output,
    ]), env=env)

    print('built %s (%d bytes)' % (output, os.path.getsize(output)))


if __name__ == '__main__':
    main()
