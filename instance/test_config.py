DEBUG = True
PRESERVE_CONTEXT_ON_EXCEPTION = False
SQLALCHEMY_TRACK_MODIFICATIONS = False

SQLALCHEMY_DATABASE_URI = 'postgresql:///pulsar-testing'
SECRET_KEY = b'a very insecure secret key'

# Redis connection parameters
REDIS_PARAMS = {
    'host': 'localhost',
    'port': 6379,
    'password': None,
    'db': None,
    'key_prefix': 'pulsar_test',
    'default_timeout': 3600 * 24 * 7,  # 1 week
    }

REQUIRE_INVITE_CODE = None
LOCKED_ACCOUNT_PERMISSIONS = {
    'view_staff_pm',
    'send_staff_pm',
    'resolve_staff_pm',
    }
INVITE_LIFETIME = 60 * 60 * 24 * 3  # 3 days

RATE_LIMIT_AUTH_SPECIFIC = (50, 80)
RATE_LIMIT_PER_USER = (80, 80)
