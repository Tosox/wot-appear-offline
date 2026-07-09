import os
import json

from appear_offline.log import log

_CONFIG_PATH = 'mods/configs/appear_offline/config.json'

_DEFAULT_CONFIG = {
    'enabled': True,
    'see_others_status': False,
}

settings = dict(_DEFAULT_CONFIG)


def load():
    if not os.path.exists(_CONFIG_PATH):
        try:
            folder = os.path.dirname(_CONFIG_PATH)
            if folder and not os.path.exists(folder):
                os.makedirs(folder)
            with open(_CONFIG_PATH, 'w') as f:
                json.dump(_DEFAULT_CONFIG, f, indent=2)
            log('created default config at ' + _CONFIG_PATH)
        except Exception as e:
            log('failed to create config: ' + str(e))
        return
    try:
        with open(_CONFIG_PATH, 'r') as f:
            settings.update(json.load(f))
        log('config loaded: ' + str(settings))
    except Exception as e:
        log('failed to load config: ' + str(e))


def save(enabled, see_others):
    settings['enabled'] = bool(enabled)
    settings['see_others_status'] = bool(see_others)
    try:
        folder = os.path.dirname(_CONFIG_PATH)
        if folder and not os.path.exists(folder):
            os.makedirs(folder)
        data = {
            'enabled': bool(settings.get('enabled', True)),
            'see_others_status': bool(settings.get('see_others_status', True)),
        }
        with open(_CONFIG_PATH, 'w') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        log('failed to save config: ' + str(e))
