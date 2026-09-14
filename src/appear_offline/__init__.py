from appear_offline.log import log
from appear_offline.util import safe


class AppearOfflineMod(object):

    @safe
    def init(self):
        from appear_offline import config, patch, ui
        config.load()
        patch.apply_patch()
        ui.register_ui()
        ui.install_contacts_settings_probe()
        log('loaded')

    @safe
    def fini(self):
        from appear_offline import patch, ui
        ui.remove_contacts_settings_probe()
        ui.unregister_ui()
        patch.remove_patch()
        log('unloaded')


g_appearOfflineMod = AppearOfflineMod()
