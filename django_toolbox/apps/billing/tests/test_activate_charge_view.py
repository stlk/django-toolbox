from django.shortcuts import reverse
from unittest.mock import patch

from . import ShopifyViewTest


@patch("shopify.RecurringApplicationCharge.find", autospec=True)
class ActivateChargeViewTest(ShopifyViewTest):
    def test_sucessfully_activates_charge(self, charge_find):
        charge_find.return_value.status = "accepted"
        charge_find.return_value.attributes = {"status": "accepted"}

        response = self.client.get(
            reverse("billing:activate-charge")
            + f"?charge_id=1&myshopify_domain={self.shop.myshopify_domain}"
        )

        self.assertRedirects(response, expected_url="/success/")
