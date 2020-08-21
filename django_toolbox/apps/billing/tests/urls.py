from django.urls import path, include
from django.http import HttpResponse

urlpatterns = [
    path("", include("django_toolbox.apps.billing.urls", namespace="billing")),
    path("login/", include("shopify_auth.urls")),
    path("success/", lambda request: HttpResponse("text"), name="success"),
]
