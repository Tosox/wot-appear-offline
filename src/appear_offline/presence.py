# -*- coding: utf-8 -*-
"""XMPP presence patching for the Appear Offline mod.

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
* true  - "invisible": broadcast AVAILABLE once so the server keeps sending you
  contacts' presence, then send each contact a *directed* UNAVAILABLE so THEY
  see you offline. You still see everyone. Caveat: currently-online contacts may
  see a brief online->offline flicker at login (their client gets the server
  broadcast a moment before your directed offline arrives). Inherent to doing
  this client-side.
* false - "hard offline": broadcast UNAVAILABLE. Fully offline to the server;
  you also stop seeing others' live status. Simplest, no flicker.

The patch is installed ONCE and reads config live, so a setting change is picked
up on the next login automatically; toggling never forces a presence send (no
rate-limit cost, no touching the live session).

Limitations: cannot lie selectively; does not touch the external clan-portal
website. Must comply with Wargaming's Fair Play Policy.
"""
from appear_offline import config
from appear_offline.log import log

# Saved original so remove_patch() can restore the game's behavior.
_orig_sendPresence = None
# Whether we subscribed to the status event (invisible mode only).
_status_listener_active = False


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


def _patched_sendPresence(self, initial=False):
    """Single presence patch that reads the CURRENT config every time the game
    sends presence (at login and battle/garage scope switches). Installed ONCE
    at init and left in place, so a setting change is picked up on the next login
    automatically -- we never force a presence send when the user toggles, so
    toggling costs nothing against the rate limit and doesn't touch the live
    session. It also only ever rides the game's own presence sends."""
    if not config.settings.get('enabled', True):
        # Mod off: behave exactly like the game (online).
        return _orig_sendPresence(self, initial)
    client = self.client()
    if not client or not client.isConnected():
        return False
    if config.settings.get('see_others_status', True):
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
    if not (config.settings.get('enabled', True) and config.settings.get('see_others_status', True)):
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
        log('hide-from-contact failed: ' + str(e))


def apply_patch():
    """Install the presence patch + status listener ONCE. Both read the config
    live, so the mode is (re)applied automatically at each login and we never
    have to touch presence when the user toggles a setting."""
    global _orig_sendPresence, _status_listener_active
    try:
        from messenger.proto.xmpp.contacts import _UserPresence
    except Exception as e:
        log('could not import _UserPresence, mod inactive: ' + str(e))
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
            log('could not subscribe to status updates: ' + str(e))
    log('presence patch armed (your setting applies at each login)')
    return True


def remove_patch():
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
        log('presence patch removed - you appear online again')
    except Exception as e:
        log('failed to restore presence: ' + str(e))
