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

# Load up Murmur slice file into Ice
Ice.loadSlice('', ['-I' + Ice.getSliceDir(), os.path.join(settings.MURMUR_ROOT, settings.SLICE_FILE)])
import Murmur

# Configure Ice properties
props = Ice.createProperties()
props.setProperty("Ice.ImplicitContext", "Shared")
props.setProperty('Ice.Default.EncodingVersion', '1.0')
idata = Ice.InitializationData()
idata.properties = props

# Create Ice connection
ice = Ice.initialize(idata)
proxy = ice.stringToProxy(settings.ICE_HOST.encode('ascii'))
secret = settings.ICE_SECRET.encode('ascii')
if secret != '':
	ice.getImplicitContext().put("secret", secret)
meta = Murmur.MetaPrx.checkedCast(proxy)

# Load route endpoints
from app import api