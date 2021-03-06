from ralph.settings import *  # noqa

DEBUG = False

TEST_DB_ENGINE = os.environ.get('TEST_DB_ENGINE', 'sqlite')

if TEST_DB_ENGINE == 'mysql':
    # use default mysql settings
    if not os.environ.get('DATABASE_PASSWORD'):
        DATABASES['default']['PASSWORD'] = None
else:  # use sqlite as default
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': ':memory:',
            'ATOMIC_REQUESTS': True,
        }
    }

INSTALLED_APPS += (
    'ralph.lib.mixins',
    'ralph.tests',
    'ralph.lib.permissions.tests',
    'ralph.lib.polymorphic.tests',
)

PASSWORD_HASHERS = ('django_plainpasswordhasher.PlainPasswordHasher',)

STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'

ROOT_URLCONF = 'ralph.urls.test'
# specify all url modules to reload during specific tests
# see `ralph.tests.mixins.ReloadUrlsMixin` for details
URLCONF_MODULES = ['ralph.urls.base', ROOT_URLCONF]
