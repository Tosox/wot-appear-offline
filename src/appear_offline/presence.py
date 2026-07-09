from appear_offline import config
from appear_offline.log import log

_orig_sendPresence = None
_status_listener_active = False


def _get_client():
    try:
        from messenger.proto.xmpp.gloox_wrapper import ClientHolder
        client = ClientHolder().client()
        if client and getattr(client, 'isConnected', None) and client.isConnected():
            return client
    except Exception:
        pass
    return None


def _send_broadcast_available(user_presence, client):
    from messenger.proto.xmpp.gloox_constants import PRESENCE
    from messenger.proto.xmpp.extensions.shared_queries import PresenceQuery
    try:
        query = user_presence._UserPresence__createQuery(PRESENCE.AVAILABLE)
    except Exception:
        query = PresenceQuery(PRESENCE.AVAILABLE)
    client.sendPresence(query)
    try:
        client.setClientPresence(PRESENCE.AVAILABLE)
    except Exception:
        pass


def _hide_from_contact(client, jid):
    from messenger.proto.xmpp.gloox_constants import PRESENCE
    from messenger.proto.xmpp.extensions.shared_queries import PresenceQuery
    query = PresenceQuery(PRESENCE.UNAVAILABLE, to=str(jid))
    client.sendPresence(query)


def _patched_sendPresence(self, initial=False):
    if initial:
        try:
            from appear_offline import ui
            ui.notify_current_status()
        except Exception as e:
            log('status notify failed: ' + str(e))
    if not config.settings.get('enabled', True):
        return _orig_sendPresence(self, initial)
    client = self.client()
    if not client or not client.isConnected():
        return False
    if config.settings.get('see_others_status', True):
        if initial:
            _send_broadcast_available(self, client)
        return True
    from messenger.proto.xmpp.gloox_constants import PRESENCE
    from messenger.proto.xmpp.extensions.shared_queries import PresenceQuery
    client.sendPresence(PresenceQuery(PRESENCE.UNAVAILABLE))
    try:
        client.setClientPresence(PRESENCE.UNAVAILABLE)
    except Exception:
        pass
    return True


def _onUserStatusUpdated(user):
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
