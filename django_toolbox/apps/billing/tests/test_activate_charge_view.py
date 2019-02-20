from django.test import override_settings
from django.shortcuts import reverse
from unittest.mock import patch

from . import ShopifyViewTest


@patch("shopify.RecurringApplicationCharge.find", autospec=True)
class ActivateChargeViewTest(ShopifyViewTest):
    def test_sucessfully_activates_charge(self, charge_find):
        charge_find.return_value.status = "accepted"
        charge_find.return_value.attributes = {"status": "accepted"}

        response = self.client.get(reverse("billing:activate-charge") + "?charge_id=1")

        self.assertRedirects(response, expected_url="/success/")
