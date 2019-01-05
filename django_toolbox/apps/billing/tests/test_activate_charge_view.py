from django.test import override_settings
from django.shortcuts import reverse
from unittest.mock import patch

from . import ShopifyViewTest

from shopify_auth.models import AbstractShopUser
from django.db import models


class AuthAppShopUserWithCurrency(AbstractShopUser):
    class Meta:
        app_label = "shopify_auth"

    currency = models.CharField(max_length=50)


@patch("shopify.RecurringApplicationCharge.find", autospec=True)
class ActivateChargeViewTest(ShopifyViewTest):
    def test_sucessfully_activates_charge(self, charge_find):
        charge_find.return_value.status = "active"
        charge_find.return_value.attributes = {"status": "active"}

        response = self.client.get(reverse("billing:activate-charge") + "?charge_id=1")

        self.assertContains(response, "Thank you")

    @override_settings(AUTH_USER_MODEL="shopify_auth.AuthAppShopUserWithCurrency")
    def test_sets_currency(self, charge_find):
        charge_find.return_value.status = "active"
        charge_find.return_value.attributes = {"status": "active"}

        self.shop = AuthAppShopUserWithCurrency.objects.create(
            myshopify_domain="test.myshopify.com"
        )
        self.client.force_login(self.shop)

        response = self.client.get(reverse("billing:activate-charge") + "?charge_id=1")

        user = AuthAppShopUserWithCurrency.objects.get()
        self.assertEqual(user.currency, "CZK")
