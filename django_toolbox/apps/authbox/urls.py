from django.urls import path, include
from . import views

app_name = "authbox"

urlpatterns = [
    path("logout", views.logout, name="logout"),
    path("disconnect", views.disconnect, name="disconnect"),
    path("", include("social_django.urls", namespace="social")),
]
