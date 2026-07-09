from appear_offline import config
from appear_offline import translations
from appear_offline.log import log

HOOK_LINKAGE = 'AppearOfflineHookUI'
HOOK_SWF = 'appear_offline_contacts_hook.swf'

_ui_registered = False
_hook_view = None
_cs_orig_populate = None


def _push_notify(body):
    import gui.SystemMessages as SystemMessages
    from gui.shared.formatters import text_styles

    title = translations.label('notify_title')
    message = text_styles.middleTitle(title) + '\n' + text_styles.main(body)
    SystemMessages.pushMessage(message, type=SystemMessages.SM_TYPE.Warning)


def notify_current_status():
    key = 'notify_current_status_offline' if config.settings['enabled'] else 'notify_current_status_online'
    _push_notify(translations.label(key))


def reconfigure(enabled, see_others):
    try:
        config.save(enabled, see_others)
        _push_notify(translations.label('notify_reconnect_body'))
    except Exception:
        import traceback
        log('reconfigure failed:\n' + traceback.format_exc())


def _load_hook_view():
    from gui.app_loader.settings import APP_NAME_SPACE
    from gui.shared.personality import ServicesLocator
    from gui.Scaleform.framework.managers.loaders import SFViewLoadParams

    app = ServicesLocator.appLoader.getApp(APP_NAME_SPACE.SF_LOBBY)
    if not app:
        return

    from helpers import dependency
    from skeletons.gui.impl import IGuiLoader
    parent = dependency.instance(IGuiLoader).windowsManager.getMainWindow()
    app.loadView(SFViewLoadParams(HOOK_LINKAGE, parent=parent))


def _onAppInitialized(event):
    from gui.app_loader.settings import APP_NAME_SPACE
    try:
        if event.ns == APP_NAME_SPACE.SF_LOBBY:
            _load_hook_view()
    except Exception:
        import traceback
        log('hook view load failed:\n' + traceback.format_exc())


def register_ui():
    global _ui_registered

    # Re-entry after a previous load - just make sure the view is up
    if _ui_registered:
        _load_hook_view()
        return

    from gui.Scaleform.framework import g_entitiesFactories, ViewSettings, ScopeTemplates
    from gui.Scaleform.framework.entities.View import View
    from gui.shared import g_eventBus, EVENT_BUS_SCOPE
    from gui.shared.events import AppLifeCycleEvent
    from frameworks.wulf import WindowLayer

    class _AppearOfflineHookView(View):

        def getAppearOfflineSettings(self):
            return {
                'enabled': config.settings['enabled'],
                'seeOthers': config.settings['see_others_status'],
                'labelEnabled': translations.label('enabled'),
                'labelSeeOthers': translations.label('see_others'),
                'seeOthersTooltip': translations.label('see_others_tooltip'),
            }

        def setAppearOfflineSettings(self, enabled, seeOthers):
            reconfigure(enabled, seeOthers)

        def pyLog(self, msg):
            pass

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

    # Register the hidden hook view and (re)load it whenever the lobby comes up
    g_entitiesFactories.addSettings(ViewSettings(
        HOOK_LINKAGE, _AppearOfflineHookView, HOOK_SWF,
        WindowLayer.WINDOW, None, ScopeTemplates.GLOBAL_SCOPE))
    g_eventBus.addListener(AppLifeCycleEvent.INITIALIZED,
                           _onAppInitialized, scope=EVENT_BUS_SCOPE.GLOBAL)

    _ui_registered = True
    _load_hook_view()


def unregister_ui():
    from gui.shared import g_eventBus, EVENT_BUS_SCOPE
    from gui.shared.events import AppLifeCycleEvent

    g_eventBus.removeListener(AppLifeCycleEvent.INITIALIZED,
                              _onAppInitialized, scope=EVENT_BUS_SCOPE.GLOBAL)


def install_contacts_settings_probe():
    global _cs_orig_populate

    from messenger.gui.Scaleform.view.lobby.ContactsSettingsView import ContactsSettingsView
    if _cs_orig_populate is None:
        _cs_orig_populate = ContactsSettingsView._populate

    # Whenever the real settings panel populates, inject our two checkboxes
    def _probe(self):
        _cs_orig_populate(self)
        _trigger_contacts_injection()

    ContactsSettingsView._populate = _probe


def _trigger_contacts_injection():
    try:
        if _hook_view is not None and _hook_view.flashObject is not None:
            _hook_view.flashObject.injectContacts()
    except Exception:
        import traceback
        log('contacts injection failed:\n' + traceback.format_exc())
