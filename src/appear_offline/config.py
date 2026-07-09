import os
import json

from appear_offline.log import log

_CONFIG_PATH = 'mods/configs/appear_offline/config.json'

_DEFAULT_CONFIG = {
    'enabled': True,
    'see_others_status': False,
}

settings = dict(_DEFAULT_CONFIG)


def _write(data):
    folder = os.path.dirname(_CONFIG_PATH)
    if folder and not os.path.exists(folder):
        os.makedirs(folder)

    with open(_CONFIG_PATH, 'w') as f:
        json.dump(data, f, indent=2)


def load():
    if not os.path.exists(_CONFIG_PATH):
        _write(_DEFAULT_CONFIG)
        return

    try:
        with open(_CONFIG_PATH, 'r') as f:
            settings.update(json.load(f))
    except Exception:
        import traceback
        log('config load failed, using defaults:\n' + traceback.format_exc())


def save(enabled, see_others):
    settings['enabled'] = bool(enabled)
    settings['see_others_status'] = bool(see_others)
    _write(settings)
