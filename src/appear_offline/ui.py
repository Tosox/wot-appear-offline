from appear_offline import config
from appear_offline import translations
from appear_offline.log import log
from appear_offline.util import safe

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


def _reconfigure(enabled, see_others, visible_to_clan):
    config.save(enabled, see_others, visible_to_clan)
    _push_notify(translations.label('notify_reconnect_body'))


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


@safe
def _onAppInitialized(event):
    from gui.app_loader.settings import APP_NAME_SPACE
    if event.ns == APP_NAME_SPACE.SF_LOBBY:
        _load_hook_view()


@safe
def _trigger_contacts_injection():
    if _hook_view and _hook_view.flashObject:
        _hook_view.flashObject.injectContacts()


def notify_current_status():
    if not config.settings['enabled']:
        key = 'notify_current_status_online'
    elif config.settings['visible_to_clanmates']:
        key = 'notify_current_status_offline_clan'
    else:
        key = 'notify_current_status_offline'
    _push_notify(translations.label(key))


def install_contacts_settings_probe():
    global _cs_orig_populate

    from messenger.gui.Scaleform.view.lobby.ContactsSettingsView import ContactsSettingsView
    if _cs_orig_populate is None:
        _cs_orig_populate = ContactsSettingsView._populate

    # Whenever the real settings panel populates, inject our checkboxes
    def _probe(self):
        _cs_orig_populate(self)
        _trigger_contacts_injection()

    ContactsSettingsView._populate = _probe


def remove_contacts_settings_probe():
    global _cs_orig_populate
    if _cs_orig_populate is None:
        return

    from messenger.gui.Scaleform.view.lobby.ContactsSettingsView import ContactsSettingsView
    ContactsSettingsView._populate = _cs_orig_populate
    _cs_orig_populate = None


def register_ui():
    global _ui_registered

    # Re-entry after a previous load
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
            try:
                return {
                    'enabled': config.settings['enabled'],
                    'seeOthers': config.settings['see_others_status'],
                    'visibleToClan': config.settings['visible_to_clanmates'],
                    'labelEnabled': translations.label('enabled'),
                    'labelSeeOthers': translations.label('see_others'),
                    'seeOthersTooltip': translations.label('see_others_tooltip'),
                    'labelVisibleToClan': translations.label('visible_to_clan'),
                    'visibleToClanTooltip': translations.label('visible_to_clan_tooltip'),
                }
            except Exception:
                import traceback
                log('settings read failed:\n' + traceback.format_exc())
                en = translations.LABELS['en']
                return {
                    'enabled': config.settings['enabled'],
                    'seeOthers': config.settings['see_others_status'],
                    'visibleToClan': config.settings['visible_to_clanmates'],
                    'labelEnabled': en['enabled'],
                    'labelSeeOthers': en['see_others'],
                    'seeOthersTooltip': en['see_others_tooltip'],
                    'labelVisibleToClan': en['visible_to_clan'],
                    'visibleToClanTooltip': en['visible_to_clan_tooltip'],
                }

        @safe
        def setAppearOfflineSettings(self, enabled, seeOthers, visibleToClan):
            _reconfigure(enabled, seeOthers, visibleToClan)

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

    # Register the hidden hook view and load it whenever the lobby comes up
    g_entitiesFactories.addSettings(ViewSettings(
        HOOK_LINKAGE, _AppearOfflineHookView, HOOK_SWF,
        WindowLayer.WINDOW, None, ScopeTemplates.GLOBAL_SCOPE))
    g_eventBus.addListener(AppLifeCycleEvent.INITIALIZED,
                           _onAppInitialized, scope=EVENT_BUS_SCOPE.GLOBAL)

    _ui_registered = True
    _load_hook_view()


def unregister_ui():
    global _ui_registered
    if not _ui_registered:
        return

    from gui.Scaleform.framework import g_entitiesFactories
    from gui.shared import g_eventBus, EVENT_BUS_SCOPE
    from gui.shared.events import AppLifeCycleEvent

    g_eventBus.removeListener(AppLifeCycleEvent.INITIALIZED,
                              _onAppInitialized, scope=EVENT_BUS_SCOPE.GLOBAL)
    g_entitiesFactories.removeSettings(HOOK_LINKAGE)
    _ui_registered = False
