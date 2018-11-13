import django.dispatch

app_installed = django.dispatch.Signal(providing_args=["request"])
