import configparser
import re
import os
import hashlib
import logging.config


"""
Django settings for webui project.

Generated by 'django-admin startproject' using Django 2.1.3.

For more information on this file, see
https://docs.djangoproject.com/en/2.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.1/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

CONFIG_FILE = '/etc/pcw.ini'

ALLOWED_HOSTS = ['*']

CSRF_TRUSTED_ORIGINS = ['https://' + os.getenv('DOMAINNAME', os.uname().nodename)]

DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'


# Application definition

INSTALLED_APPS = [
    'ocw.apps.OcwConfig',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_tables2',
    'django_filters',
    'bootstrap4',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'webui.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'webui.wsgi.application'


# Database
# https://docs.djangoproject.com/en/2.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db', 'db.sqlite3'),
    }
}


# Password validation
# https://docs.djangoproject.com/en/2.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.'
                + 'UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.'
                + 'MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.'
                + 'CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.'
                + 'NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/2.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.1/howto/static-files/
STATIC_ROOT = os.path.join(BASE_DIR, "static/")

STATIC_URL = '/static/'

logging.config.dictConfig({
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'console': {
            'format': '%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'console',
        },
    },
    'loggers': {
        '': {
            'level': 'WARNING',
            'handlers': ['console'],
        },
        'ocw': {
            'level': 'INFO',
            'handlers': ['console'],
            'propagate': False,
        }
    },
})


class ConfigFile:
    __instance = None
    __file_hash = None
    filename = None
    config = None

    def __new__(cls, filename=None):
        if ConfigFile.__instance is None:
            ConfigFile.__instance = object.__new__(cls)
        ConfigFile.__instance.filename = filename or CONFIG_FILE
        return ConfigFile.__instance

    def get_hash(self):
        with open(self.filename, 'r') as f:
            h = hashlib.sha256()
            h.update(f.read().encode('utf-8'))
            return h.hexdigest()

    def check_file(self):
        file_hash = self.get_hash()
        if self.__file_hash is None or self.__file_hash != file_hash:
            self.__file_hash = file_hash
            self.config = configparser.ConfigParser()
            self.config.read(self.filename)

    def get(self, config_path: str, default=None):
        self.check_file()
        config_pointer = self.config
        config_array = config_path.split('/')
        for i in config_array:
            if i in config_pointer:
                config_pointer = config_pointer[i]
            else:
                if default is None:
                    raise LookupError('Missing attribute {} in file {}'.format(config_path, self.filename))
                return default
        return config_pointer

    def getList(self, config_path: str, default: list = []) -> list:
        return [i.strip() for i in self.get(config_path, ','.join(default)).split(',')]


class PCWConfig():

    @staticmethod
    def get_feature_property(feature: str, property: str, namespace: str = None):
        default_values = {
            'cleanup/max-age-hours': {'default': 24 * 7, 'return_type': int},
            'cleanup/azure-storage-resourcegroup': {'default': 'openqa-upload', 'return_type': str},
            'cleanup/azure-storage-account-name': {'default': 'openqa', 'return_type': str},
            'cleanup/ec2-max-age-days': {'default': -1, 'return_type': int},
            'updaterun/default_ttl': {'default': 44400, 'return_type': int},
            'notify/to': {'default': None, 'return_type': str},
            'notify/age-hours': {'default': 12, 'return_type': int},
            'cluster.notify/to': {'default': None, 'return_type': str},
            'notify/smtp': {'default': None, 'return_type': str},
            'notify/smtp-port': {'default': 25, 'return_type': int},
            'notify/from': {'default': 'pcw@publiccloud.qa.suse.de', 'return_type': str},
            'webui/openqa_url': {'default': 'https://openqa.suse.de', 'return_type': str}
        }
        key = '/'.join([feature, property])
        if key not in default_values:
            raise LookupError("Missing {} in default_values list".format(key))
        if namespace:
            setting = '{}.namespace.{}/{}'.format(feature, namespace, property)
            if PCWConfig.has(setting):
                return default_values[key]['return_type'](ConfigFile().get(setting))
        return default_values[key]['return_type'](
            ConfigFile().get(key, default_values[key]['default']))

    @staticmethod
    def get_namespaces_for(feature: str) -> list:
        if PCWConfig.has(feature):
            return ConfigFile().getList('{}/namespaces'.format(feature), ConfigFile().getList('default/namespaces'))
        return list()

    @staticmethod
    def get_providers_for(feature: str, namespace: str):
        return ConfigFile().getList('{}.namespace.{}/providers'.format(feature, namespace),
                                    ConfigFile().getList('{}/providers'.format(feature), ['ec2', 'azure', 'gce']))

    @staticmethod
    def has(setting: str) -> bool:
        try:
            ConfigFile().get(setting)
            return True
        except LookupError:
            return False

    @staticmethod
    def getBoolean(config_path: str, namespace: str = None, default=False) -> bool:
        if namespace:
            (feature, property) = config_path.split('/')
            setting = '{}.namespace.{}/{}'.format(feature, namespace, property)
            if PCWConfig.has(setting):
                value = ConfigFile().get(setting)
            else:
                value = ConfigFile().get(config_path, default)
        else:
            value = ConfigFile().get(config_path, default)
        if isinstance(value, bool):
            return value
        return bool(re.match("^(true|on|1|yes)$", str(value), flags=re.IGNORECASE))


def build_absolute_uri(path=''):
    ''' Create a absolute url from given path. You could use reverse() to create a path which points to a specific
    view.
    Parameters:
    -----------
    path : (optional) give the path which will appended to the base URL

    Example:
    --------
         url = build_absolute_uri(reverse(views.delete, args=[i.id]))
    '''
    base_url = ConfigFile().get('default/base-url', "publiccloud.qa.suse.de")

    if not re.match('^http', base_url):
        base_url = 'https://{}'.format(base_url)

    base_url = re.sub('/+$', '', base_url)

    if len(path) == 0:
        return base_url

    if not re.match('^/', path):
        path = '/{}'.format(path)

    return base_url + path
