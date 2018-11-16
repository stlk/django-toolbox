from django.test import TestCase, override_settings
from unittest.mock import patch, PropertyMock

from shopify_auth.models import AbstractShopUser


class AuthAppShopUser(AbstractShopUser):
    class Meta:
        app_label = "shopify_auth"


@override_settings(AUTH_USER_MODEL="shopify_auth.AuthAppShopUser")
class ShopifyViewTest(TestCase):
    def setUp(self):
        super(TestCase, self).setUp()

        self.shop_patcher = patch("shopify.Shop", autospec=True)
        mck = self.shop_patcher.start()
        mck.current().currency = "CZK"
        self.addCleanup(self.shop_patcher.stop)

        self.shop = AuthAppShopUser.objects.create(
            myshopify_domain="test.myshopify.com"
        )
        self.client.force_login(self.shop)
