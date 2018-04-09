DEBUG = True
PRESERVE_CONTEXT_ON_EXCEPTION = False
SQLALCHEMY_TRACK_MODIFICATIONS = False

SQLALCHEMY_DATABASE_URI = 'postgresql:///pulsar-testing'
REDIS_URL = 'redis:///0'
SECRET_KEY = b'a very insecure secret key'

SITE_PRIVATE = True
REQUIRE_INVITE_CODE = None
INVITE_LIFETIME = 60 * 60 * 24 * 3  # 3 days
