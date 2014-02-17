"""
settings.py

All default settings.

:copyright: (C) 2014 by github.com/alfg.
:license:   MIT, see README for more details.
"""

import os

APP_HOST = '0.0.0.0'
APP_PORT = 5000
APP_DEBUG = True

ICE_HOST = 'Meta:tcp -h localhost -p 6502'
SLICE_FILE = 'Murmur.ice'

MURMUR_ROOT = os.path.dirname(os.path.abspath(__file__))

ENABLE_AUTH = False
USERS = {
    "admin": "admin",
}
