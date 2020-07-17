from django.shortcuts import reverse
from django.test import TestCase
import responses
from shopify_auth.models import AbstractShopUser

from django_toolbox.shopify_graphql_test import mock_response

from . import ShopifyViewTest


ANNUAL_CHARGE_MUTATION = {
    "appSubscriptionCreate": {
        "appSubscription": {"id": "gid://shopify/AppSubscription/15887990828"},
        "confirmationUrl": "https://stepanka-dev.myshopify.com/admin/charges/15887990828/confirm_recurring_application_charge?signature=BAh7BzoHaWRsKwgsgP%2ByAwA6EmF1dG9fYWN0aXZhdGVU--9823ef9eee3d0e9174a29a6378bf5a28570f3d3e",
        "userErrors": [],
    }
}

SUBSCRIPTION_QUERY = {
    "appInstallation": {
        "activeSubscriptions": [
            {
                "name": "Candy Rack - Basic",
                "status": "ACTIVE",
                "test": True,
                "trialDays": 14,
                "currentPeriodEnd": "2020-07-14T11:50:41Z",
                "lineItems": [
                    {
                        "plan": {
                            "pricingDetails": {
                                "interval": "ANNUAL",
                                "price": {"amount": "29.99"},
                            }
                        }
                    }
                ],
            }
        ]
    }
}


class CreateAnnualChargeViewTest(ShopifyViewTest):
    @responses.activate
    def test_annual_charge_created(self):
        shop = self.shop
        self.client.force_login(shop)
        mock_response(SUBSCRIPTION_QUERY)
        mock_response(ANNUAL_CHARGE_MUTATION)

        response = self.client.get(
            reverse("billing:create-annual-charge"), content_type="application/json"
        )

        self.assertContains(response, "confirm_recurring_application_charge")
