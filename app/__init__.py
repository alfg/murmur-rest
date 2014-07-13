"""
murmur-rest

__init__.py
Initialize murmur-rest project.

:copyright: (C) 2014 by github.com/alfg.
:license:   MIT, see README for more details.
"""

import os

from flask import Flask
from flask.ext.httpauth import HTTPDigestAuth
import settings

import Ice

# Create Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)

# Initialize Digest Auth
auth = HTTPDigestAuth()

# If enabled, all endpoints will be digest auth protected
auth_enabled = settings.ENABLE_AUTH

# Load up Murmur slice file into Ice and create connection
Ice.loadSlice('', ['-I' + Ice.getSliceDir(), os.path.join(settings.MURMUR_ROOT, settings.SLICE_FILE)])
import Murmur
ice = Ice.initialize()
proxy = ice.stringToProxy(settings.ICE_HOST.encode('ascii'))
meta = Murmur.MetaPrx.checkedCast(proxy)

# Load route endpoints
from app import api