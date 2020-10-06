import time
from django.conf import settings
from intercom.client import Client


class IntercomWebhooks:
    def __init__(self):
        self.app = settings.APP_NAME
        self.intercom = Client(personal_access_token=settings.INTERCOM_ACCESS_TOKEN)

    def create_intercom_event(self, myshopify_domain, event_name):
        self.intercom.events.create(
            event_name=f"{self.app}-uninstalled",
            created_at=int(time.mktime(time.localtime())),
            user_id=myshopify_domain,
        )

    def app_installed(self, shopify_shop):
        if settings.INTERCOM_ACCESS_TOKEN:
            self.intercom.users.create(
                user_id=shopify_shop.myshopify_domain,
                email=shopify_shop.email,
                name=shopify_shop.shop_owner,
                phone=shopify_shop.phone,
                custom_attributes={"plan_name": shopify_shop.plan_name},
            )
            self.create_intercom_event(
                shopify_shop.myshopify_domain, f"{self.app}-installed"
            )
            self.intercom.tags.tag(
                name=f"{self.app}", users=[{"user_id": shopify_shop.myshopify_domain}]
            )
            self.intercom.tags.tag(
                name=f"{self.app}-customer",
                users=[{"user_id": shopify_shop.myshopify_domain}],
            )

    def app_uninstalled(self, myshopify_domain):
        if settings.INTERCOM_ACCESS_TOKEN:
            self.intercom.events.create(
                event_name=f"{self.app}-uninstalled",
                created_at=int(time.mktime(time.localtime())),
                user_id=myshopify_domain,
            )
            self.create_intercom_event(myshopify_domain, f"{self.app}-uninstalled")
            self.intercom.tags.untag(
                name=f"{self.app}-annual", users=[{"user_id": myshopify_domain}]
            )
            self.intercom.tags.untag(
                name=f"{self.app}-customer", users=[{"user_id": myshopify_domain}]
            )

    def activate_annual_billing(self, myshopify_domain):
        if settings.INTERCOM_ACCESS_TOKEN:
            self.create_intercom_event(myshopify_domain, f"{self.app}-annual")
            self.intercom.tags.tag(
                name=f"{self.app}-annual", users=[{"user_id": myshopify_domain}]
            )
