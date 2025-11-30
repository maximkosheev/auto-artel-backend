import os

from dotenv import load_dotenv

from .settings import *

DEBUG = True

SECRET_KEY = 'django-insecure-b5#8^@!2e_(vspz)nv&0ksnh6g&sou$=6+rl*vu*iv#dq8_0at'

load_dotenv(os.path.join(BASE_DIR, '.env'))

ALLOWED_HOSTS = ['localhost', '127.0.0.1']

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'simple': {
            'format': '%(asctime)s %(levelname)s %(message)s'
        },
    },
    'handlers': {
        'root': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': 'auto-artel.log',
            'formatter': 'simple'
        },
        'api': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': 'auto-artel-api.log',
            'formatter': 'simple'
        },
    },
    'loggers': {
        'root': {
            'handlers': ['root'],
            'level': 'INFO',
            'propagate': False,
        },
        'api.views': {
            'handlers': ['api'],
            'level': 'DEBUG',
            'propagate': False
        }
    },
}


CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer"
    }
}
