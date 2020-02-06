from setuptools import setup, find_packages

setup(
    name="django-toolbox",
    version="1.4.0",
    author="Josef Rousek",
    author_email="josef@rousek.name",
    packages=find_packages(
        include=["django_toolbox", "django_toolbox.apps", "django_toolbox.apps.billing"]
    ),
    include_package_data=True,
    url="https://github.com/stlk/django-toolbox",
    license="MIT",
    description="Collection of useful Django snippets",
    install_requires=[
        "django>=2",
        "shopifyapi>=5",
        "django-shopify-auth",
        "requests",
        "elastic-apm",
        "social-auth-app-django",
        "python-jose",
        "ua-parser",
        "django-rq",
    ],
)
