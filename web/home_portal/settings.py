"""
Django settings for home_portal project.

Generated by 'django-admin startproject' using Django 4.0.2.

For more information on this file, see
https://docs.djangoproject.com/en/4.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.0/ref/settings/
"""

from pathlib import Path

import configparser

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
# SECRET_KEY = 'y=q1#z_ltet+$wq3wz5$21)3))r6g*gr!^t155m(8puo0n$bpu'
# Read the secret key from a file
with open('/deploy/secret_key.txt') as f:
    SECRET_KEY = f.read().strip()

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True
ALLOWED_HOSTS = ['127.0.0.1']
CSRF_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_SECURE = not DEBUG

# Keep the session cookie valid for 14 days (in seconds)
SESSION_COOKIE_AGE = 1209600

# Import global settings file
settings = configparser.ConfigParser()
settings.read(BASE_DIR / 'settings.txt')

# Convert setting from external file in variables
FEATURE_CONSUMPTION       = settings.getint('FEATURE_FLAGS', 'CONSUMPTION', fallback=1)
FEATURE_GAS               = settings.getint('FEATURE_FLAGS', 'GAS', fallback=1)
FEATURE_PRODUCTION        = settings.getint('FEATURE_FLAGS', 'PRODUCTION', fallback=1)
FEATURE_SOLAR_CONSUMPTION = settings.getint('FEATURE_FLAGS', 'SOLAR_CONSUMPTION', fallback=1)

# Application definition

INSTALLED_APPS = [
    'home_energy.apps.HomeEnergyConfig',
    'home_heating.apps.HomeHeatingConfig',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
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

ROOT_URLCONF = 'home_portal.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'home_portal.context_processors.feature_flags',
            ],
        },
    },
]

WSGI_APPLICATION = 'home_portal.wsgi.application'


# Database
# https://docs.djangoproject.com/en/4.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# Password validation
# https://docs.djangoproject.com/en/2.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/4.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'CET'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.0/howto/static-files/

# Tho locations where django should collect static files other than 'static' dirs in the apps
STATICFILES_DIRS = [
    BASE_DIR / "static"
]
# The URL to use when refering to static files
STATIC_URL = '/static/'
# The location where static files are put for serving them after they have been collected
STATIC_ROOT = '/var/www/html/static/'

# Default primary key field type
# https://docs.djangoproject.com/en/4.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGIN_URL = '/auth/login/'
LOGIN_REDIRECT_URL = '/home-energy/'
LOGOUT_REDIRECT_URL = '/auth/login'
