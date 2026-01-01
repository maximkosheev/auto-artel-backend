from .settings import *

DEBUG = True

ALLOWED_HOSTS = ['auto-artel.madmax-code.ru']

CSRF_TRUSTED_ORIGINS = [
    'http://auto-artel.madmax-code.ru:8000',
    'https://auto-artel.madmax-code.ru:8000'
]

CORS_ORIGIN_WHITELIST = [
    'http://auto-artel.madmax-code.ru:8000',
    'https://auto-artel.madmax-code.ru:8000'
]

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
