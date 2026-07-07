from appear_offline.log import log


class AppearOfflineMod(object):

    def init(self):
        try:
            from appear_offline import config, presence, ui
            config.load()
            presence.apply_patch()
            ui.register_ui()
            ui.install_contacts_settings_probe()
            log('loaded')
        except Exception:
            import traceback
            log('init failed:\n' + traceback.format_exc())

    def fini(self):
        try:
            from appear_offline import presence, ui
            presence.remove_patch()
            ui.unregister_ui()
            log('unloaded')
        except Exception:
            import traceback
            log('fini failed:\n' + traceback.format_exc())


g_appearOfflineMod = AppearOfflineMod()
