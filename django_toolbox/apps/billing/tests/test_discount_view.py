import datetime
from unittest.mock import patch
from django.test import TestCase
from django.shortcuts import reverse
from django.utils import timezone

from . import ShopifyViewTest
from ..pricing import generate_token, is_token_valid


class DiscountViewTest(ShopifyViewTest):
    def test_shows_discount_info(self):
        token = generate_token(
            {"price": 5, "trial_days": 10, "shop": "test.myshopify.com"}
        )

        response = self.client.get(reverse("billing:discount", args=(token,)))

        self.assertContains(response, "5 USD")
        self.assertContains(response, "<strong>10</strong> days.")


class PricingTest(TestCase):
    def test_validates_token(self):
        self.assertFalse(
            is_token_valid(
                {
                    "generated": (
                        timezone.now() - datetime.timedelta(days=45)
                    ).isoformat()
                }
            )
        )

        self.assertTrue(is_token_valid({"generated": timezone.now().isoformat()}))
