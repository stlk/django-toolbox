from django.test import TestCase, override_settings
from unittest.mock import MagicMock, patch

from shopify_auth.models import AbstractShopUser


class AuthAppShopUser(AbstractShopUser):
    class Meta:
        app_label = "shopify_auth"

    @property
    def settings(self):
        return MagicMock()


@override_settings(AUTH_USER_MODEL="shopify_auth.AuthAppShopUser")
class ShopifyViewTest(TestCase):
    def setUp(self):
        super(TestCase, self).setUp()

        self.shop_patcher = patch("shopify.Shop", autospec=True)
        mck = self.shop_patcher.start()
        mck.current().currency = "CZK"
        mck.current().iana_timezone = "Europe/Amsterdam"
        mck.current().email = "test@test.com"
        self.addCleanup(self.shop_patcher.stop)

        self.shop = AuthAppShopUser.objects.create(
            myshopify_domain="test.myshopify.com"
        )
        self.shop.settings.discounts_enabled = True
        self.client.force_login(self.shop)
