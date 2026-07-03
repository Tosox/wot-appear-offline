# -*- coding: utf-8 -*-
"""Appear Offline - World of Tanks mod.

Makes your account appear offline to friends and clanmates while you keep
playing normally. See presence.py for how it works and ui.py for the native
Contacts > Settings toggle. This package is imported by the thin entry module
scripts/client/gui/mods/mod_appear_offline.py.
"""
from appear_offline.log import log


class AppearOfflineMod(object):
    """Owns the mod lifecycle. init()/fini() are wrapped so a failure here can't
    corrupt the game's mod-loading (WoT silently swallows AttributeError during
    load, which can break this or other mods with no visible error)."""

    def init(self):
        try:
            # Imported here (not at module top) so the package imports cheaply
            # and there's no circular-import ordering to worry about.
            from appear_offline import config, presence, ui
            config.load()
            # Install the patch unconditionally: it reads config live and
            # delegates to the game's own behavior when disabled, so it's
            # harmless when off and picks up the current setting at each login.
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
