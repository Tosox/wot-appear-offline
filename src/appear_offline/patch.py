from appear_offline import config
from appear_offline.log import log


_oUserPresence__sendPresence = None
_status_listener_active = False


def _get_client():
    from messenger.proto.xmpp.gloox_wrapper import ClientHolder

    client = ClientHolder().client()
    if client and client.isConnected():
        return client
    return None


def _send_broadcast_available(user_presence, client):
    from messenger.proto.xmpp.gloox_constants import PRESENCE

    # Reuse the game's own query builder so the presence keeps its game context
    query = user_presence._UserPresence__createQuery(PRESENCE.AVAILABLE)
    client.sendPresence(query)
    client.setClientPresence(PRESENCE.AVAILABLE)


def _send_broadcast_unavailable(client):
    from messenger.proto.xmpp.gloox_constants import PRESENCE
    from messenger.proto.xmpp.extensions.shared_queries import PresenceQuery

    client.sendPresence(PresenceQuery(PRESENCE.UNAVAILABLE))
    client.setClientPresence(PRESENCE.UNAVAILABLE)


def _hide_from_contact(client, jid):
    from messenger.proto.xmpp.gloox_constants import PRESENCE
    from messenger.proto.xmpp.extensions.shared_queries import PresenceQuery

    # Directed 'unavailable' - only this contact sees us go offline
    client.sendPresence(PresenceQuery(PRESENCE.UNAVAILABLE, to=str(jid)))


def _patched_sendPresence(self, initial=False):
    try:
        # Once per login, tell the player how they now appear
        if initial:
            from appear_offline import ui
            ui.notify_current_status()

        # Mod enabled - drive presence ourselves
        if config.settings['enabled']:
            client = self.client()
            if not client or not client.isConnected():
                return False

            # Invisible: stay a live resource so the server keeps feeding us
            # other people's status; each contact is hidden by the listener
            if config.settings['see_others_status']:
                if initial:
                    _send_broadcast_available(self, client)
                return True

            # Hard offline: one global 'unavailable' hides us from everyone
            _send_broadcast_unavailable(client)
            return True
    except Exception:
        import traceback
        log('sendPresence failed:\n' + traceback.format_exc())

    # Mod disabled - let the game broadcast presence as usual
    return _oUserPresence__sendPresence(self, initial)


def _onUserStatusUpdated(user):
    # Only the invisible mode hides from contacts one by one
    if not (config.settings['enabled'] and config.settings['see_others_status']):
        return

    try:
        if user is None or user.isCurrentPlayer():
            return

        jid = user.getJID()
        client = _get_client()
        if jid and client:
            _hide_from_contact(client, jid)
    except Exception:
        import traceback
        log('hide-from-contact failed:\n' + traceback.format_exc())


def apply_patch():
    global _oUserPresence__sendPresence, _status_listener_active

    from messenger.proto.xmpp.contacts import _UserPresence
    if _oUserPresence__sendPresence is None:
        _oUserPresence__sendPresence = _UserPresence.sendPresence
    _UserPresence.sendPresence = _patched_sendPresence

    # React to contacts coming online so invisible mode can hide from them
    from messenger.proto.events import g_messengerEvents
    if not _status_listener_active:
        g_messengerEvents.users.onUserStatusUpdated += _onUserStatusUpdated
        _status_listener_active = True


def remove_patch():
    global _oUserPresence__sendPresence, _status_listener_active

    if _status_listener_active:
        from messenger.proto.events import g_messengerEvents
        g_messengerEvents.users.onUserStatusUpdated -= _onUserStatusUpdated
        _status_listener_active = False

    if _oUserPresence__sendPresence is None:
        return

    from messenger.proto.xmpp.contacts import _UserPresence
    _UserPresence.sendPresence = _oUserPresence__sendPresence
    _oUserPresence__sendPresence = None
