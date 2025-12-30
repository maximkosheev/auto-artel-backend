from .settings import *

DEBUG = True

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
            'filename': '/app/logs/auto-artel.log',
            'formatter': 'simple'
        },
        'api': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': '/app/logs/auto-artel-api.log',
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

stub()
