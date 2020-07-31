from django.urls import path
from . import views

app_name = "billing"

urlpatterns = [
    path("", views.CreateChargeView.as_view(), name="create-charge"),
    path("code/<str:code>/", views.PromoCodeView.as_view(), name="code"),
    path("activate-charge", views.ActivateChargeView.as_view(), name="activate-charge"),
    path("generate-charge", views.GenerateChargeView.as_view(), name="generate-charge"),
]
