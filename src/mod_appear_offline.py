# -*- coding: utf-8 -*-
"""Appear Offline - World of Tanks mod: entry point.

Thin shim. The WoT mod loader imports this module from
scripts/client/gui/mods/ and calls init()/fini(); all logic lives in the
top-level `appear_offline` package (scripts/client/appear_offline/).
"""
from appear_offline import g_appearOfflineMod


def init():
    g_appearOfflineMod.init()


def fini():
    g_appearOfflineMod.fini()
