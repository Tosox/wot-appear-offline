# -*- coding: utf-8 -*-
"""Native Contacts > Settings UI injection for the Appear Offline mod.

We load a small "hook" SWF (appear_offline_contacts_hook.swf) as a lobby view.
Once loaded it watches for the native Contacts settings view (alias
'ContactsSettingsView') and injects two CheckBoxes into it. The SWF calls back
into the DAAPI view class below to read/write our settings.

HOOK_LINKAGE must match the SWF's exported document-class name
(AppearOfflineHookUI, compiled by src_flash/build_swf.sh).

Toggling saves the choice and notifies the user; the change takes effect on the
next login (see presence.py for why mid-session changes are avoided).
"""
from appear_offline import config
from appear_offline import translations
from appear_offline.log import log

HOOK_LINKAGE = 'AppearOfflineHookUI'
HOOK_SWF = 'appear_offline_contacts_hook.swf'

_ui_registered = False
_hook_view = None   # live instance of our loaded hook View (to call into its SWF)
_cs_orig_populate = None


def notify_apply_on_login():
    """Tell the user the change takes effect on next login (mid-session changing
    of chat presence is not reliable on WG's server)."""
    try:
        import gui.SystemMessages as SystemMessages
        SystemMessages.pushMessage(translations.label('notify'),
                                   type=SystemMessages.SM_TYPE.Warning)
    except Exception as e:
        log('notify failed: ' + str(e))


def reconfigure(enabled, see_others):
    """From the in-game UI: save the choice and notify the user it applies on
    next login. We do NOT touch live presence: mid-session changing is unreliable
    on WG's server (global presence is rate-limited, directed presence isn't
    delivered to roster friends live, and an in-session reconnect corrupts native
    handler state). The already-installed patch reads config live, so a fresh
    login applies it cleanly."""
    config.save(enabled, see_others)
    notify_apply_on_login()
    log('reconfigured: enabled=%s see_others=%s (applies on next login)'
        % (config.settings['enabled'], config.settings['see_others_status']))


def _load_hook_view():
    try:
        from gui.app_loader.settings import APP_NAME_SPACE
        from gui.shared.personality import ServicesLocator
        from gui.Scaleform.framework.managers.loaders import SFViewLoadParams
        app = ServicesLocator.appLoader.getApp(APP_NAME_SPACE.SF_LOBBY)
        if not app:
            return
        parent = None
        try:
            from helpers import dependency
            from skeletons.gui.impl import IGuiLoader
            parent = dependency.instance(IGuiLoader).windowsManager.getMainWindow()
        except Exception:
            parent = None
        app.loadView(SFViewLoadParams(HOOK_LINKAGE, parent=parent))
    except Exception as e:
        log('could not load hook view: ' + str(e))


def _onAppInitialized(event):
    try:
        from gui.app_loader.settings import APP_NAME_SPACE
        if event.ns == APP_NAME_SPACE.SF_LOBBY:
            _load_hook_view()
    except Exception:
        pass


def register_ui():
    global _ui_registered
    if _ui_registered:
        _load_hook_view()
        return
    try:
        from gui.Scaleform.framework import g_entitiesFactories, ViewSettings, ScopeTemplates
        from gui.Scaleform.framework.entities.View import View
        from gui.shared import g_eventBus, EVENT_BUS_SCOPE
        from gui.shared.events import AppLifeCycleEvent
        from frameworks.wulf import WindowLayer

        class _AppearOfflineHookView(View):
            # Methods below are bound by the DAAPI bridge to the same-named
            # public Function vars on the Flash side.

            def getAppearOfflineSettings(self):
                return {
                    'enabled': bool(config.settings.get('enabled', True)),
                    'seeOthers': bool(config.settings.get('see_others_status', True)),
                    'labelEnabled': translations.label('enabled'),
                    'labelSeeOthers': translations.label('see_others'),
                    'seeOthersTooltip': translations.label('see_others_tooltip'),
                }

            def setAppearOfflineSettings(self, enabled, seeOthers):
                # Saves the choice + notifies; takes effect on next login.
                reconfigure(enabled, seeOthers)

            def pyLog(self, msg):
                pass   # AS3 debug hook; silent in release builds

            def _populate(self):
                global _hook_view
                super(_AppearOfflineHookView, self)._populate()
                _hook_view = self

            def _dispose(self):
                global _hook_view
                if _hook_view is self:
                    _hook_view = None
                super(_AppearOfflineHookView, self)._dispose()

            def onFocusIn(self, alias):
                if self._isDAAPIInited():
                    return False

        g_entitiesFactories.addSettings(ViewSettings(
            HOOK_LINKAGE, _AppearOfflineHookView, HOOK_SWF,
            WindowLayer.WINDOW, None, ScopeTemplates.GLOBAL_SCOPE))
        g_eventBus.addListener(AppLifeCycleEvent.INITIALIZED,
                               _onAppInitialized, scope=EVENT_BUS_SCOPE.GLOBAL)
        _ui_registered = True
        _load_hook_view()
        log('UI hook registered')
    except Exception as e:
        log('UI registration failed (mod still works without UI): ' + str(e))


def unregister_ui():
    try:
        from gui.shared import g_eventBus, EVENT_BUS_SCOPE
        from gui.shared.events import AppLifeCycleEvent
        g_eventBus.removeListener(AppLifeCycleEvent.INITIALIZED,
                                  _onAppInitialized, scope=EVENT_BUS_SCOPE.GLOBAL)
    except Exception:
        pass


# --- trigger the SWF injection when the native Contacts settings view opens ---
# That view is a sub-view that doesn't fire VIEW_LOADED on the main loader, so we
# patch its _populate to tell our hook SWF to inject the two checkboxes.

def install_contacts_settings_probe():
    global _cs_orig_populate
    try:
        from messenger.gui.Scaleform.view.lobby.ContactsSettingsView import ContactsSettingsView
        if _cs_orig_populate is None:
            _cs_orig_populate = ContactsSettingsView._populate

        def _probe(self):
            _cs_orig_populate(self)
            _trigger_contacts_injection()

        ContactsSettingsView._populate = _probe
    except Exception as e:
        log('could not hook ContactsSettingsView: ' + str(e))


def _trigger_contacts_injection():
    """Ask our loaded hook SWF to find the contacts settings view and inject."""
    try:
        if _hook_view is not None and getattr(_hook_view, 'flashObject', None) is not None:
            _hook_view.flashObject.injectContacts()
    except Exception as e:
        log('contacts injection trigger failed: ' + str(e))
