from django.urls import path
from . import views

app_name = "backoffice_common"

urlpatterns = [
    path(
        "manage-script?shop_id=<int:shop_id>",
        views.ManageScriptView.as_view(),
        name="manage-script",
    ),
    path("theme-liquid", views.ThemeLiquidView.as_view(), name="theme-liquid"),
    path("configuration", views.ConfigurationView.as_view(), name="configuration"),
]
