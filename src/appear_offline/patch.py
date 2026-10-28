from appear_offline import config
from appear_offline.log import log
from appear_offline.util import safe


_oUserPresence__sendPresence = None
_oMUCProvider__joinToRoom = None
_status_listener_active = False

# Stands in for MUCProvider.joinToRoom's own default, which lives in a game
# module we must not import until the client has booted
_JOIN_RESULT_DEFAULT = object()


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


@safe
def _onUserStatusUpdated(user):
    # Only the invisible mode hides from contacts one by one
    if not (config.settings['enabled'] and config.settings['see_others_status']):
        return

    if user is None or user.isCurrentPlayer():
        return

    jid = user.getJID()
    client = _get_client()
    if jid and client:
        _hide_from_contact(client, jid)


@safe
def _blocks_clan_join(muc_provider, room_jid):
    # Clanmates read our status off the clan room's occupant list, and MUC has
    # no invisible occupant - staying out of the room is the only way to hide
    if not config.settings['enabled'] or config.settings['visible_to_clanmates']:
        return False

    from messenger.proto.xmpp.find_criteria import XmppClanChannelCriteria

    channel = muc_provider.channelsStorage.getChannelByCriteria(XmppClanChannelCriteria())
    return channel is not None and channel.getID() == room_jid


def _patched_joinToRoom(self, roomJID, password='', name='', initResult=_JOIN_RESULT_DEFAULT):
    if _blocks_clan_join(self, roomJID):
        return (True, None)

    if initResult is _JOIN_RESULT_DEFAULT:
        from messenger.proto.xmpp.messages.muc import ACTION_RESULT
        initResult = ACTION_RESULT.SHOW_ROOM

    return _oMUCProvider__joinToRoom(self, roomJID, password, name, initResult)


def apply_patch():
    global _oUserPresence__sendPresence, _oMUCProvider__joinToRoom, _status_listener_active

    from messenger.proto.xmpp.contacts import _UserPresence
    if _oUserPresence__sendPresence is None:
        _oUserPresence__sendPresence = _UserPresence.sendPresence
    _UserPresence.sendPresence = _patched_sendPresence

    from messenger.proto.xmpp.messages.muc import MUCProvider
    if _oMUCProvider__joinToRoom is None:
        _oMUCProvider__joinToRoom = MUCProvider.joinToRoom
    MUCProvider.joinToRoom = _patched_joinToRoom

    # React to contacts coming online so invisible mode can hide from them
    from messenger.proto.events import g_messengerEvents
    if not _status_listener_active:
        g_messengerEvents.users.onUserStatusUpdated += _onUserStatusUpdated
        _status_listener_active = True


def remove_patch():
    global _oUserPresence__sendPresence, _oMUCProvider__joinToRoom, _status_listener_active

    if _status_listener_active:
        from messenger.proto.events import g_messengerEvents
        g_messengerEvents.users.onUserStatusUpdated -= _onUserStatusUpdated
        _status_listener_active = False

    if _oMUCProvider__joinToRoom is not None:
        from messenger.proto.xmpp.messages.muc import MUCProvider
        MUCProvider.joinToRoom = _oMUCProvider__joinToRoom
        _oMUCProvider__joinToRoom = None

    if _oUserPresence__sendPresence is None:
        return

    from messenger.proto.xmpp.contacts import _UserPresence
    _UserPresence.sendPresence = _oUserPresence__sendPresence
    _oUserPresence__sendPresence = None
