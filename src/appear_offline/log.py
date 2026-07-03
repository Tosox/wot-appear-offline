# -*- coding: utf-8 -*-
"""Tiny logging helper for the Appear Offline mod.

Leaf module: every other appear_offline module imports `log` from here, so none
of them has to reach back into the package __init__ (which would risk a circular
import). Output lands in the game's python.log, tagged for easy grepping.
"""

TAG = '[appear_offline]'


def log(msg):
    print(TAG + ' ' + msg)
