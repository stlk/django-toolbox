import sys
import django
from django.conf import settings


def billing_function(shop):
    return (5, 3, "test subscription")


configuration = {
    "DEBUG": True,
    "DATABASES": {"default": {"ENGINE": "django.db.backends.sqlite3"}},
    "INSTALLED_APPS": [
        "django.contrib.auth",
        "django.contrib.contenttypes",
        "django.contrib.sessions",
        "shopify_auth",
        "django_toolbox.apps.billing",
    ],
    "AUTHENTICATION_BACKENDS": ["shopify_auth.backends.ShopUserBackend"],
    "TEMPLATES": [
        {"BACKEND": "django.template.backends.django.DjangoTemplates", "APP_DIRS": True}
    ],
    "ROOT_URLCONF": "django_toolbox.apps.billing.tests.urls",
    "SHOPIFY_APP_NAME": "Test App",
    "SHOPIFY_APP_API_KEY": "test-api-key",
    "SHOPIFY_APP_API_SECRET": "test-api-secret",
    "SHOPIFY_APP_API_SCOPE": ["read_products"],
    "SHOPIFY_APP_IS_EMBEDDED": True,
    "SHOPIFY_APP_DEV_MODE": False,
    "SHOPIFY_APP_TEST_CHARGE": False,
    "SHOPIFY_APP_API_VERSION": "2020-01",
    "BILLING_FUNCTION": billing_function,
    "BILLING_REDIRECT_URL": "success",
    "APP_NAME": "test_app_name",
    "MIDDLEWARE": [
        "django.middleware.common.CommonMiddleware",
        "django.contrib.sessions.middleware.SessionMiddleware",
        "django.middleware.csrf.CsrfViewMiddleware",
        "django.contrib.auth.middleware.AuthenticationMiddleware",
        "django.contrib.messages.middleware.MessageMiddleware",
    ],
}

settings.configure(**configuration)

django.setup()

from django.test.runner import DiscoverRunner

test_runner = DiscoverRunner()
default_tests = [
    "test_graphql_client",
    "django_toolbox.apps.billing",
    "django_toolbox.discounts",
]

if len(sys.argv[1:]) > 0:
    tests = sys.argv[1:]
else:
    tests = default_tests

failures = test_runner.run_tests(tests)
if failures:
    sys.exit(failures)
