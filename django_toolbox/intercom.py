import time
from django.conf import settings
from intercom.client import Client


APP_NAME = settings.APP_NAME
intercom = Client(personal_access_token=settings.INTERCOM_ACCESS_TOKEN)


def create_intercom_event(myshopify_domain, event_name):
    intercom.events.create(
        event_name=f"{APP_NAME}-uninstalled",
        created_at=int(time.mktime(time.localtime())),
        user_id=myshopify_domain,
    )


def app_installed(shopify_shop):
    if settings.INTERCOM_ACCESS_TOKEN:
        intercom.users.create(
            user_id=shopify_shop.myshopify_domain,
            email=shopify_shop.email,
            name=shopify_shop.shop_owner,
            phone=shopify_shop.phone,
            custom_attributes={"plan_name": shopify_shop.plan_name},
        )
        create_intercom_event(shopify_shop.myshopify_domain, f"{APP_NAME}-installed")
        intercom.tags.tag(
            name=f"{APP_NAME}", users=[{"user_id": shopify_shop.myshopify_domain}]
        )
        intercom.tags.tag(
            name=f"{APP_NAME}-customer",
            users=[{"user_id": shopify_shop.myshopify_domain}],
        )


def app_uninstalled(myshopify_domain):
    if settings.INTERCOM_ACCESS_TOKEN:
        intercom.events.create(
            event_name=f"{APP_NAME}-uninstalled",
            created_at=int(time.mktime(time.localtime())),
            user_id=myshopify_domain,
        )
        create_intercom_event(myshopify_domain, f"{APP_NAME}-uninstalled")
        intercom.tags.untag(
            name=f"{APP_NAME}-annual", users=[{"user_id": myshopify_domain}]
        )
        intercom.tags.untag(
            name=f"{APP_NAME}-customer", users=[{"user_id": myshopify_domain}]
        )


def activate_annual_billing(myshopify_domain):
    if settings.INTERCOM_ACCESS_TOKEN:
        create_intercom_event(myshopify_domain, f"{APP_NAME}-annual")
        intercom.tags.tag(
            name=f"{APP_NAME}-annual", users=[{"user_id": myshopify_domain}]
        )
