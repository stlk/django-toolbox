from decimal import Decimal

from ..pricing import calculate_subscription_pricing
from . import ShopifyViewTest

SUBSCRIPTION_NODE_ANNUAL = {
    "lineItems": [
        {
            "plan": {
                "pricingDetails": {"interval": "ANNUAL", "price": {"amount": "287.90"}}
            }
        }
    ]
}


SUBSCRIPTION_NODE_MONTHLY = {
    "lineItems": [
        {
            "plan": {
                "pricingDetails": {
                    "interval": "EVERY_30_DAYS",
                    "price": {"amount": "29.99"},
                }
            }
        }
    ]
}

TWOPLACES = Decimal(10) ** -2


class SubscriptionDataTest(ShopifyViewTest):
    def test_get_annual_subscription_data(self):
        subscription_data = calculate_subscription_pricing(SUBSCRIPTION_NODE_ANNUAL)
        expected_data = {
            "monthly_subscription_price": Decimal(29.99).quantize(TWOPLACES),
            "annual_subscription_price": Decimal(287.90).quantize(TWOPLACES),
            "annual_subscription_price_monthly": Decimal(23.99).quantize(TWOPLACES),
            "interval": "ANNUAL",
        }
        self.assertEqual(subscription_data, expected_data)

    def test_get_monthly_subscription_data(self):
        subscription_data = calculate_subscription_pricing(SUBSCRIPTION_NODE_MONTHLY)
        expected_data = {
            "monthly_subscription_price": Decimal(29.99).quantize(TWOPLACES),
            "annual_subscription_price": Decimal(287.90).quantize(TWOPLACES),
            "annual_subscription_price_monthly": Decimal(23.99).quantize(TWOPLACES),
            "interval": "EVERY_30_DAYS",
        }
        self.assertEqual(subscription_data, expected_data)
