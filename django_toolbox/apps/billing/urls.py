from django.urls import path
from . import views

app_name = "billing"

urlpatterns = [
    path("", views.CreateChargeView.as_view(), name="create-charge"),
    path("activate-charge", views.ActivateChargeView.as_view(), name="activate-charge"),
    path("discount/<str:token>/", views.DiscountView.as_view(), name="discount"),
    path(
        "generate-discount",
        views.GenerateDiscountView.as_view(),
        name="generate-discount",
    ),
]
