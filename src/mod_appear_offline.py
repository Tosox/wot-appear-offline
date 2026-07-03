# -*- coding: utf-8 -*-
"""
Appear Offline - World of Tanks mod

Makes your account appear offline to friends and clanmates while you keep
playing normally, WITHOUT losing your own view of their online status.

How presence works in WoT
-------------------------
Your client publishes presence over XMPP (gloox). The Python method
`messenger.proto.xmpp.contacts._UserPresence.sendPresence()` broadcasts
PRESENCE.AVAILABLE in the garage (AVAILABLE/DND in battle). gloox never
broadcasts on its own, so that method fully controls what contacts see.

The catch: the XMPP server only pushes your contacts' presence to you while
YOU are an "available" resource. So simply broadcasting UNAVAILABLE (the naive
"appear offline") also blinds you to everyone else.

Two modes (config: "see_others_status")
----------------------------------------
* true  (default) - "invisible": broadcast AVAILABLE once so the server keeps
  sending you contacts' presence, then send each contact a *directed*
  UNAVAILABLE so THEY see you offline. You still see everyone.
  Caveat: currently-online contacts may see a brief online->offline flicker at
  login (their client gets the server broadcast a moment before your directed
  offline arrives). Inherent to doing this client-side.

* false - "hard offline": broadcast UNAVAILABLE. Fully offline to the server;
  you also stop seeing others' live status. Simplest, no flicker.

Limitations: cannot lie selectively; does not touch the external clan-portal
website. Must comply with Wargaming's Fair Play Policy.
"""
import os
import json

TAG = '[appear_offline]'

_CONFIG_PATH = 'res_mods/configs/appear_offline/config.json'

_DEFAULT_CONFIG = {
    # Master switch. Set to false to disable the mod without uninstalling it.
    'enabled': True,
    # true  -> invisible (appear offline but still see others' status)
    # false -> hard offline (appear offline, also stop seeing others)
    'see_others_status': False,
}

_config = dict(_DEFAULT_CONFIG)

# Saved originals so fini() can restore the game's behavior.
_orig_sendPresence = None
# Whether we subscribed to the status event (invisible mode only).
_status_listener_active = False


# --- config ------------------------------------------------------------------

def _load_config():
    if not os.path.exists(_CONFIG_PATH):
        try:
            folder = os.path.dirname(_CONFIG_PATH)
            if folder and not os.path.exists(folder):
                os.makedirs(folder)
            with open(_CONFIG_PATH, 'w') as f:
                json.dump(_DEFAULT_CONFIG, f, indent=2)
            print(TAG + ' created default config at ' + _CONFIG_PATH)
        except Exception as e:
            print(TAG + ' failed to create config: ' + str(e))
        return
    try:
        with open(_CONFIG_PATH, 'r') as f:
            _config.update(json.load(f))
        print(TAG + ' config loaded: ' + str(_config))
    except Exception as e:
        print(TAG + ' failed to load config: ' + str(e))


def _save_config():
    try:
        folder = os.path.dirname(_CONFIG_PATH)
        if folder and not os.path.exists(folder):
            os.makedirs(folder)
        data = {
            'enabled': bool(_config.get('enabled', True)),
            'see_others_status': bool(_config.get('see_others_status', True)),
        }
        with open(_CONFIG_PATH, 'w') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(TAG + ' failed to save config: ' + str(e))


# --- helpers -----------------------------------------------------------------

def _get_client():
    """Return the live XMPP client (or None if not connected)."""
    try:
        from messenger.proto.xmpp.gloox_wrapper import ClientHolder
        client = ClientHolder().client()
        if client and getattr(client, 'isConnected', None) and client.isConnected():
            return client
    except Exception:
        pass
    return None


def _send_broadcast_available(user_presence, client):
    """Announce AVAILABLE to the server so it keeps feeding us contacts' presence.

    Reuses the game's own query builder (host + IGR metadata) when possible so
    the stanza looks exactly like a normal one.
    """
    from messenger.proto.xmpp.gloox_constants import PRESENCE
    from messenger.proto.xmpp.extensions.shared_queries import PresenceQuery
    try:
        # name-mangled _UserPresence.__createQuery
        query = user_presence._UserPresence__createQuery(PRESENCE.AVAILABLE)
    except Exception:
        query = PresenceQuery(PRESENCE.AVAILABLE)
    client.sendPresence(query)
    try:
        client.setClientPresence(PRESENCE.AVAILABLE)
    except Exception:
        pass


def _hide_from_contact(client, jid):
    """Send a directed UNAVAILABLE to one contact so they see us offline."""
    from messenger.proto.xmpp.gloox_constants import PRESENCE
    from messenger.proto.xmpp.extensions.shared_queries import PresenceQuery
    query = PresenceQuery(PRESENCE.UNAVAILABLE, to=str(jid))
    client.sendPresence(query)



def _notify_apply_on_login():
    """Tell the user the change takes effect on next login (mid-session changing
    of chat presence is not reliable on WG's server)."""
    try:
        import gui.SystemMessages as SystemMessages
        SystemMessages.pushMessage(_label('notify'),
                                   type=SystemMessages.SM_TYPE.Warning)
    except Exception as e:
        print(TAG + ' notify failed: ' + str(e))


def _reconfigure(enabled, see_others):
    """From the in-game UI: save the choice, arm the login patch, and notify the
    user it applies on next login. We do NOT touch live presence: mid-session
    changing is unreliable on WG's server (global presence is rate-limited,
    directed presence isn't delivered to roster friends live, and an in-session
    reconnect corrupts native handler state). A fresh login applies it cleanly."""
    _config['enabled'] = bool(enabled)
    _config['see_others_status'] = bool(see_others)
    _save_config()
    # NOTHING is done to the live session: the patch is already installed and
    # reads config live, so this just changes what happens at the next login.
    _notify_apply_on_login()
    print(TAG + ' reconfigured: enabled=%s see_others=%s (applies on next login)'
          % (_config['enabled'], _config['see_others_status']))


# --- patched presence --------------------------------------------------------

def _patched_sendPresence(self, initial=False):
    """Single presence patch that reads the CURRENT config every time the game
    sends presence (at login and battle/garage scope switches). It is installed
    ONCE at init and left in place, so a setting change is picked up on the next
    login automatically -- we never force a presence send when the user toggles,
    so toggling costs nothing against the rate limit and doesn't touch the live
    session. It also only ever rides the game's own presence sends (never adds
    extra ones)."""
    if not _config.get('enabled', True):
        # Mod off: behave exactly like the game (online).
        return _orig_sendPresence(self, initial)
    client = self.client()
    if not client or not client.isConnected():
        return False
    if _config.get('see_others_status', True):
        # Invisible: stay AVAILABLE (so we keep seeing others) and hide via the
        # reactive listener; suppress scope-switch re-broadcasts to stay hidden.
        if initial:
            _send_broadcast_available(self, client)
        return True
    # Hard offline: go globally UNAVAILABLE.
    from messenger.proto.xmpp.gloox_constants import PRESENCE
    from messenger.proto.xmpp.extensions.shared_queries import PresenceQuery
    client.sendPresence(PresenceQuery(PRESENCE.UNAVAILABLE))
    try:
        client.setClientPresence(PRESENCE.UNAVAILABLE)
    except Exception:
        pass
    return True


def _onUserStatusUpdated(user):
    """When a contact comes online they can see us, so send them a directed
    'unavailable'. Reads config live: only acts in invisible mode."""
    if not (_config.get('enabled', True) and _config.get('see_others_status', True)):
        return
    try:
        if user is None or user.isCurrentPlayer():
            return
        jid = user.getJID()
        if not jid:
            return
        client = _get_client()
        if client is None:
            return
        _hide_from_contact(client, jid)
    except Exception as e:
        print(TAG + ' hide-from-contact failed: ' + str(e))


# --- apply / remove ----------------------------------------------------------

def _apply_patch():
    """Install the presence patch + status listener ONCE. Both read the config
    live, so the mode is (re)applied automatically at each login and we never
    have to touch presence when the user toggles a setting."""
    global _orig_sendPresence, _status_listener_active
    try:
        from messenger.proto.xmpp.contacts import _UserPresence
    except Exception as e:
        print(TAG + ' could not import _UserPresence, mod inactive: ' + str(e))
        return False
    if _orig_sendPresence is None:
        _orig_sendPresence = _UserPresence.sendPresence
    _UserPresence.sendPresence = _patched_sendPresence
    if not _status_listener_active:
        try:
            from messenger.proto.events import g_messengerEvents
            g_messengerEvents.users.onUserStatusUpdated += _onUserStatusUpdated
            _status_listener_active = True
        except Exception as e:
            print(TAG + ' could not subscribe to status updates: ' + str(e))
    print(TAG + ' presence patch armed (your setting applies at each login)')
    return True


def _remove_patch():
    global _status_listener_active
    if _status_listener_active:
        try:
            from messenger.proto.events import g_messengerEvents
            g_messengerEvents.users.onUserStatusUpdated -= _onUserStatusUpdated
        except Exception:
            pass
        _status_listener_active = False
    if _orig_sendPresence is None:
        return
    try:
        from messenger.proto.xmpp.contacts import _UserPresence
        _UserPresence.sendPresence = _orig_sendPresence
        print(TAG + ' presence patch removed - you appear online again')
    except Exception as e:
        print(TAG + ' failed to restore presence: ' + str(e))


# --- native UI (Contacts > Settings injection) -------------------------------
#
# We reuse a small "hook" SWF (appear_offline_contacts_hook.swf) that, once
# loaded as a lobby view, watches for the native Contacts settings view
# (alias 'ContactsSettingsView') and injects two CheckBoxes into it. The SWF
# calls back into the Python view class below to read/write our settings.
#
# HOOK_LINKAGE must match the SWF's exported document-class name
# (AppearOfflineHookUI, compiled by as3/build_swf.sh).

HOOK_LINKAGE = 'AppearOfflineHookUI'
HOOK_SWF = 'appear_offline_contacts_hook.swf'

_LABELS = {
    'en': {'enabled': 'Appear offline',
           'see_others': "Still see others' status",
           'see_others_tooltip': "{HEADER}Still see others' status{/HEADER}{BODY}Keeps you connected to chat so you can still see your friends' online status while you appear offline to them.\n\nBecause of this, friends may briefly see you come online right after you log in, before you disappear again.\n\n<img src='img://gui/maps/icons/library/icon_alert_32x32.png' width='18' height='18' vspace='-5'/> <font color='#FF9900'>This is an experimental option.</font>{/BODY}",
           'notify': 'Appear Offline: this change will take effect after your next login.'},
    'de': {'enabled': 'Offline erscheinen',
           'see_others': 'Status anderer weiterhin sehen',
           'see_others_tooltip': "{HEADER}Status anderer weiterhin sehen{/HEADER}{BODY}Haelt dich mit dem Chat verbunden, sodass du den Online-Status deiner Freunde weiterhin sehen kannst, waehrend du fuer sie offline erscheinst.\n\nDeshalb sehen Freunde dich evtl. kurz online, direkt nachdem du dich eingeloggt hast, bevor du wieder verschwindest.\n\n<img src='img://gui/maps/icons/library/icon_alert_32x32.png' width='18' height='18' vspace='-5'/> <font color='#FF9900'>Dies ist eine experimentelle Option.</font>{/BODY}",
           'notify': 'Offline erscheinen: Diese Aenderung wird nach dem naechsten Login wirksam.'},
}

_ui_registered = False
_hook_view = None   # live instance of our loaded hook View (to call into its SWF)


def _label(key):
    try:
        from helpers import getClientLanguage
        lang = getClientLanguage()
    except Exception:
        lang = 'en'
    return _LABELS.get(lang, _LABELS['en']).get(key, key)


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
        print(TAG + ' could not load hook view: ' + str(e))


def _onAppInitialized(event):
    try:
        from gui.app_loader.settings import APP_NAME_SPACE
        if event.ns == APP_NAME_SPACE.SF_LOBBY:
            _load_hook_view()
    except Exception:
        pass


def _register_ui():
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
                    'enabled': bool(_config.get('enabled', True)),
                    'seeOthers': bool(_config.get('see_others_status', True)),
                    'labelEnabled': _label('enabled'),
                    'labelSeeOthers': _label('see_others'),
                    'seeOthersTooltip': _label('see_others_tooltip'),
                }

            def setAppearOfflineSettings(self, enabled, seeOthers):
                # Saves the choice + notifies; takes effect on next login.
                _reconfigure(enabled, seeOthers)

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
        print(TAG + ' UI hook registered')
    except Exception as e:
        print(TAG + ' UI registration failed (mod still works without UI): ' + str(e))


def _unregister_ui():
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
_cs_orig_populate = None


def _install_contacts_settings_probe():
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
        print(TAG + ' could not hook ContactsSettingsView: ' + str(e))


def _trigger_contacts_injection():
    """Ask our loaded hook SWF to find the contacts settings view and inject."""
    try:
        if _hook_view is not None and getattr(_hook_view, 'flashObject', None) is not None:
            _hook_view.flashObject.injectContacts()
    except Exception as e:
        print(TAG + ' contacts injection trigger failed: ' + str(e))


def init():
    _load_config()
    # Install the patch unconditionally: it reads config live and delegates to
    # the game's own behavior when disabled, so it's harmless when off and picks
    # up the current setting at every login.
    _apply_patch()
    _register_ui()   # register so the toggle is reachable in-game
    _install_contacts_settings_probe()
    print(TAG + ' loaded')


def fini():
    _remove_patch()
    _unregister_ui()
    print(TAG + ' unloaded')
