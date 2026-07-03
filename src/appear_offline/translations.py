# -*- coding: utf-8 -*-
"""User-facing strings (en/de) for the Appear Offline mod.

Kept as a plain Python module (not JSON): there are only a handful of labels,
so a dict + lookup is simpler than a file loader. The `see_others_tooltip`
values use WoT's complex-tooltip markup ({HEADER}/{BODY}, inline <img>/<font>).
"""

LABELS = {
    'en': {'enabled': 'Appear offline',
           'see_others': "Still see others' status",
           'see_others_tooltip': "{HEADER}Still see others' status{/HEADER}{BODY}Keeps you connected to chat so you can still see your friends' online status while you appear offline to them.\n\nBecause of this, friends may briefly see you come online right after you log in, before you disappear again.\n\n<img src='img://gui/maps/icons/library/icon_alert_32x32.png' width='18' height='18' vspace='-5'/> <font color='#FF9900'>This is an experimental option.</font>{/BODY}",
           'notify_title': 'Appear Offline',
           'notify_body': 'This change will take effect after your next login.'},
    'de': {'enabled': 'Offline erscheinen',
           'see_others': 'Status anderer weiterhin sehen',
           'see_others_tooltip': "{HEADER}Status anderer weiterhin sehen{/HEADER}{BODY}Haelt dich mit dem Chat verbunden, sodass du den Online-Status deiner Freunde weiterhin sehen kannst, waehrend du fuer sie offline erscheinst.\n\nDeshalb sehen Freunde dich evtl. kurz online, direkt nachdem du dich eingeloggt hast, bevor du wieder verschwindest.\n\n<img src='img://gui/maps/icons/library/icon_alert_32x32.png' width='18' height='18' vspace='-5'/> <font color='#FF9900'>Dies ist eine experimentelle Option.</font>{/BODY}",
           'notify_title': 'Offline erscheinen',
           'notify_body': 'Diese Aenderung wird nach dem naechsten Login wirksam.'},
}


def label(key):
    try:
        from helpers import getClientLanguage
        lang = getClientLanguage()
    except Exception:
        lang = 'en'
    return LABELS.get(lang, LABELS['en']).get(key, key)
