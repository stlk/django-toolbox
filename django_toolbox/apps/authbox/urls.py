from django.urls import path, include
from . import views

app_name = "authbox"

urlpatterns = [
    path("logout", views.logout, name="logout"),
    path("new-user", views.new_user),
    path("", include("social_django.urls", namespace="social")),
]
