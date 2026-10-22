"""
Django settings for plus_market project.
"""
import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent


# .env faylini (agar mavjud bo'lsa) o'qiymiz. python-dotenv o'rnatilmagan bo'lsa ham
# loyiha ishlayveradi — u holda haqiqiy environment o'zgaruvchilari ishlatiladi.
try:
    from dotenv import load_dotenv
    load_dotenv(BASE_DIR / ".env")
except ImportError:
    pass


def _env_bool(name, default=False):
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in ("1", "true", "yes", "on")


DEBUG = _env_bool("DEBUG", default=False)

# SECRET_KEY kodda saqlanmaydi. Faqat DEBUG=True (lokal) bo'lsa vaqtinchalik kalit ishlatiladi;
# productionda kalit berilmasa loyiha ishga tushmaydi.
SECRET_KEY = os.environ.get("SECRET_KEY", "")
if not SECRET_KEY:
    if DEBUG:
        SECRET_KEY = "django-insecure-faqat-lokal-dev-uchun"
    else:
        raise RuntimeError("SECRET_KEY topilmadi. .env faylga SECRET_KEY=... qo'shing (.env.example'ga qarang).")

ALLOWED_HOSTS = [h.strip() for h in os.environ.get("ALLOWED_HOSTS", "127.0.0.1,localhost").split(",") if h.strip()]


INSTALLED_APPS = [
    "unfold",
    "unfold.contrib.filters",
    "unfold.contrib.forms",

    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    "product",
]


MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    'whitenoise.middleware.WhiteNoiseMiddleware',
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "plus_market.urls"



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
                'product.context_processors.cart_count',
            ],
        },
    },
]


DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}




AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]





STATICFILES_DIRS = [BASE_DIR / "product" / "static"]


MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"



DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


LANGUAGE_CODE = 'uz'
TIME_ZONE = 'Asia/Tashkent'
USE_I18N = True
USE_TZ = True


AUTH_USER_MODEL = 'product.CustomUser'

LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'home'
LOGOUT_REDIRECT_URL = 'home'


UNFOLD = {
    "SITE_TITLE": "Plus Market",
    "SITE_HEADER": "Plus Market — Boshqaruv paneli",
    "SITE_URL": "/",
    "DASHBOARD_CALLBACK": None,
    "COLORS": {
        "primary": {
            "50": "240 253 244",
            "100": "220 252 231",
            "200": "187 247 208",
            "300": "134 239 172",
            "400": "74 222 128",
            "500": "34 197 94",
            "600": "22 163 74",
            "700": "21 128 61",
            "800": "22 101 52",
            "900": "20 83 45",
            "950": "5 46 22",
        },
    },
    "SIDEBAR": {
        "show_search": True,
        "show_all_applications": True,
    },
    "STYLES": [
        lambda request: """
            :root {
                --color-font-default: #0f172a !important;
                --color-font-subtle: #334155 !important;
                --color-font-muted: #475569 !important;
            }
            body, table, td, th, input, select, textarea, label, span, p, div, a {
                color: #0f172a !important;
                font-weight: 500 !important;
            }
            .dark body, .dark table, .dark td, .dark th, .dark input, .dark select, .dark textarea, .dark label, .dark span, .dark p, .dark div, .dark a {
                color: #f8fafc !important;
            }
        """
    ]
}

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'