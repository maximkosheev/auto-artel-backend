from .settings import *

DEBUG = False

ALLOWED_HOSTS = [os.getenv('ALLOWED_HOST')]

CSRF_TRUSTED_ORIGINS = [
    f'https://{os.getenv('ALLOWED_HOST')}'
]

CORS_ORIGIN_WHITELIST = [
    f'https://{os.getenv('ALLOWED_HOST')}'
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
