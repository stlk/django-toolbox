from django.shortcuts import reverse
from unittest.mock import patch

from . import ShopifyViewTest


class ActivateChargeViewTest(ShopifyViewTest):
    @patch("shopify.RecurringApplicationCharge.find", autospec=True)
    def test_sucessfully_activates_charge(self, charge_find):
        charge_find.return_value.status = "active"
        charge_find.return_value.attributes = {"status": "active"}

        response = self.client.get(reverse("billing:activate-charge") + "?charge_id=1")

        self.assertContains(response, "Thank you")
