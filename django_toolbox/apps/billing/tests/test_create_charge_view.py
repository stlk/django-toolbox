from django.test import override_settings
from django.db import models
from unittest.mock import patch
from shopify_auth.models import AbstractShopUser
import shopify

from ..views import CreateChargeView
from . import ShopifyViewTest


class AuthAppShopUserWithCurrency(AbstractShopUser):
    class Meta:
        app_label = "shopify_auth"

    currency = models.CharField(max_length=50)


class CreateChargeViewTest(ShopifyViewTest):
    @patch("shopify.RecurringApplicationCharge", autospec=True)
    def test_redirects_to_charge(self, charge_mock):
        charge_mock.current.return_value = None

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

    @override_settings(BILLING_FUNCTION=None)
    @patch("shopify.RecurringApplicationCharge", autospec=True)
    def test_should_charge_return_false_when_there_is_no_charge_and_billing_is_disabled(
        self, charge_mock
    ):
        charge_mock.current.return_value = None

        view = CreateChargeView()
        view.shop = shopify.Shop()
        view.shop.plan_name = "shopify"
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

    @override_settings(SHOPIFY_APP_TEST_CHARGE=False)
    @override_settings(AUTH_USER_MODEL="shopify_auth.AuthAppShopUserWithCurrency")
    @patch("shopify.RecurringApplicationCharge", autospec=True)
    def test_should_charge_return_false_when_there_IS_charge_and_shop_is_not_dev(
        self, charge_mock
    ):
        charge_mock.current.return_value = shopify.RecurringApplicationCharge()

        self.shop = AuthAppShopUserWithCurrency.objects.create(
            myshopify_domain="test-currency.myshopify.com"
        )
        self.client.force_login(self.shop)

        response = self.client.get("/")
        self.assertRedirects(response, expected_url="/success/")

        user = AuthAppShopUserWithCurrency.objects.get()
        self.assertEqual(user.currency, "CZK")
