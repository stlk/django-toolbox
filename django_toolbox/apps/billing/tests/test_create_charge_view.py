from django.test import override_settings
from django.shortcuts import reverse
from unittest.mock import patch
import shopify

from ..pricing import generate_token
from ..views import CreateChargeView
from . import ShopifyViewTest


class CreateChargeViewTest(ShopifyViewTest):
    @patch("shopify.RecurringApplicationCharge", autospec=True)
    def test_redirects_to_charge(self, charge_mock):
        charge_mock.current.return_value = None

        with self.assertTemplateUsed("billing/redirect.html"):
            response = self.client.get("/")

    @patch("shopify.RecurringApplicationCharge", autospec=True)
    def test_redirects_to_charge_with_discount(self, charge_mock):
        charge_mock.current.return_value = None
        token = generate_token(
            {"price": 5, "trial_days": 10, "shop": "test.myshopify.com"}
        )
        self.client.get(reverse("billing:discount", args=(token,)))

        with self.assertTemplateUsed("billing/redirect.html"):
            response = self.client.get("/")

    @override_settings(SHOPIFY_APP_TEST_CHARGE=False)
    @patch("shopify.RecurringApplicationCharge", autospec=True)
    def test_should_charge_return_true_when_there_is_no_charge_and_shop_is_not_dev(
        self, charge_mock
    ):
        charge_mock.current.return_value = None

        view = CreateChargeView()
        view.shop = shopify.Shop()
        view.shop.plan_name = "basic"
        self.assertTrue(view.should_charge())

    @override_settings(SHOPIFY_APP_TEST_CHARGE=False)
    @patch("shopify.RecurringApplicationCharge", autospec=True)
    def test_should_charge_return_false_when_there_IS_charge_and_shop_is_not_dev(
        self, charge_mock
    ):
        charge_mock.current.return_value = shopify.RecurringApplicationCharge()

        view = CreateChargeView()
        view.shop = shopify.Shop()
        view.shop.plan_name = "basic"
        self.assertFalse(view.should_charge())

    @override_settings(SHOPIFY_APP_TEST_CHARGE=False)
    @patch("shopify.RecurringApplicationCharge", autospec=True)
    def test_should_charge_return_false_when_there_is_no_charge_and_shop_IS_dev(
        self, charge_mock
    ):
        charge_mock.current.return_value = None

        view = CreateChargeView()
        view.shop = shopify.Shop()
        view.shop.plan_name = "affiliate"
        self.assertFalse(view.should_charge())

    @override_settings(SHOPIFY_APP_TEST_CHARGE=False)
    @patch("shopify.RecurringApplicationCharge", autospec=True)
    def test_should_charge_return_false_when_there_is_no_charge_and_shop_IS_staff_business(
        self, charge_mock
    ):
        charge_mock.current.return_value = None

        view = CreateChargeView()
        view.shop = shopify.Shop()
        view.shop.plan_name = "staff_business"
        self.assertFalse(view.should_charge())

    @override_settings(SHOPIFY_APP_TEST_CHARGE=True)
    @patch("shopify.RecurringApplicationCharge", autospec=True)
    def test_should_charge_return_true_when_there_is_no_charge_and_shop_IS_dev_and_test_is_enabled(
        self, charge_mock
    ):
        charge_mock.current.return_value = None

        view = CreateChargeView()
        view.shop = shopify.Shop()
        view.shop.plan_name = "affiliate"
        self.assertTrue(view.should_charge())
