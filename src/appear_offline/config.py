import os
import json

from appear_offline.util import safe

_CONFIG_PATH = 'mods/configs/appear_offline/config.json'

_DEFAULT_CONFIG = {
    'enabled': True,
    'see_others_status': False,
    'visible_to_clanmates': False,
}

settings = dict(_DEFAULT_CONFIG)


def _write(data):
    folder = os.path.dirname(_CONFIG_PATH)
    if folder and not os.path.exists(folder):
        os.makedirs(folder)

    with open(_CONFIG_PATH, 'w') as f:
        json.dump(data, f, indent=2)


@safe
def load():
    if not os.path.exists(_CONFIG_PATH):
        _write(_DEFAULT_CONFIG)
        return

    with open(_CONFIG_PATH, 'r') as f:
        settings.update(json.load(f))


def save(enabled, see_others, visible_to_clanmates):
    settings['enabled'] = bool(enabled)
    settings['see_others_status'] = bool(see_others)
    settings['visible_to_clanmates'] = bool(visible_to_clanmates)
    _write(settings)
