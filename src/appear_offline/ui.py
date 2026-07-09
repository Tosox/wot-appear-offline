from appear_offline import config
from appear_offline import translations
from appear_offline.log import log

HOOK_LINKAGE = 'AppearOfflineHookUI'
HOOK_SWF = 'appear_offline_contacts_hook.swf'

_ui_registered = False
_hook_view = None
_cs_orig_populate = None


def _wrap_notify(body):
    title = translations.label('notify_title')
    try:
        from gui.shared.formatters import text_styles
        return text_styles.middleTitle(title) + '\n' + text_styles.main(body)
    except Exception:
        return title + ': ' + body


def notify_apply_on_login():
    try:
        import gui.SystemMessages as SystemMessages
        SystemMessages.pushMessage(_wrap_notify(translations.label('notify_reconnect_body')),
                                   type=SystemMessages.SM_TYPE.Warning)
    except Exception as e:
        log('notify failed: ' + str(e))


def notify_current_status():
    try:
        import gui.SystemMessages as SystemMessages
        if config.settings.get('enabled', True):
            str_id = 'notify_current_status_offline'
        else:
            str_id = 'notify_current_status_online'
        SystemMessages.pushMessage(_wrap_notify(translations.label(str_id)),
                                   type=SystemMessages.SM_TYPE.Warning)
    except Exception as e:
        log('status notify failed: ' + str(e))


def reconfigure(enabled, see_others):
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

            def getAppearOfflineSettings(self):
                return {
                    'enabled': bool(config.settings.get('enabled', True)),
                    'seeOthers': bool(config.settings.get('see_others_status', True)),
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
    try:
        if _hook_view is not None and getattr(_hook_view, 'flashObject', None) is not None:
            _hook_view.flashObject.injectContacts()
    except Exception as e:
        log('contacts injection trigger failed: ' + str(e))
