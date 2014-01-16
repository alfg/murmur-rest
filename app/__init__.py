import os

from flask import Flask
import settings

import Ice

# Create Flask app
app = Flask(__name__)

# Load up Murmur slice file into Ice and create connection
Ice.loadSlice('', ['-I' + Ice.getSliceDir(), os.path.join(settings.MURMUR_ROOT, settings.SLICE_FILE)])
import Murmur
ice = Ice.initialize()
proxy = ice.stringToProxy('Meta:tcp -h localhost -p 6502'.encode('ascii'))
meta = Murmur.MetaPrx.checkedCast(proxy)

# Load route endpoints
from app import views