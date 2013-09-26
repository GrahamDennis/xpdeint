#!/usr/bin/env python
# encoding: utf-8
import os

versionString = '2.1.4 "Well if this isn\'t nice, I don\'t know what is"'

if 'XMDS_USER_DATA' in os.environ:
    xpdeintUserDataPath = os.environ['XMDS_USER_DATA']
else:
    xpdeintUserDataPath = os.path.join(os.path.expanduser('~'), '.xmds')
