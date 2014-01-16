import os

APP_HOST = '0.0.0.0'
APP_PORT = 5000
APP_DEBUG = True

ICE_HOST = 'Meta:tcp -h localhost -p 6502'
SLICE_FILE = 'Murmur.ice'

MURMUR_ROOT = os.path.dirname(os.path.abspath(__file__))
