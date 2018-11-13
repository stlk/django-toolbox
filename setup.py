from setuptools import setup

setup(
    name="django-toolbox",
    version="1.0.0",
    author="Josef Rousek",
    author_email="josef@rousek.name",
    packages=["django_toolbox", "django_toolbox.apps", "django_toolbox.apps.billing"],
    url="https://github.com/stlk/django-toolbox",
    license="MIT",
    description="Collection of useful Django snippets",
)
