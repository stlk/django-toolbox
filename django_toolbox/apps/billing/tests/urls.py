from django.urls import path, include

urlpatterns = [
    path("", include("django_toolbox.apps.billing.urls", namespace="billing")),
    path("login/", include("shopify_auth.urls")),
]
