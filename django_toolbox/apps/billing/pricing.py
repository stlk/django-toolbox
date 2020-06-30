import requests

from django.conf import settings
from django.shortcuts import reverse
from django_toolbox.shopify_graphql import _check_for_errors
import shopify


ANNUAL_CHARGE_MUTATION = '''mutation AnnualSubscriptionCreate($name: String!, $return_url: URL!, $trial_days: Int!, $amount: Decimal!){
    appSubscriptionCreate(
        name: $name
        returnUrl: $return_url
        trialDays: $trial_days
        test:true
        lineItems: [
        {
            plan: {
                appRecurringPricingDetails: {
                    price: { amount: $amount, currencyCode: USD }
                    interval: ANNUAL
                }
            }
        }
        ]
    ) {
        appSubscription {
            id
        }
        confirmationUrl
        userErrors {
            field
            message
        }
    }
}
'''

def create_charge(request, shop):
    price, trial_days, name = settings.BILLING_FUNCTION(shop)

    return shopify.RecurringApplicationCharge.create(
        {
            "name": name,
            "price": price,
            "return_url": request.build_absolute_uri(
                reverse("billing:activate-charge")
            ),
            "trial_days": trial_days,
            "test": settings.SHOPIFY_APP_TEST_CHARGE,
        }
    )


def create_annual_charge(request, shop):
    price, trial_days, name = settings.ANNUAL_BILLING_FUNCTION(shop)
    return_url = request.build_absolute_uri(reverse("billing:activate-charge"))
    headers = {
        "X-Shopify-Access-Token": shop.token,
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    url = f"https://{shop.myshopify_domain}/admin/api/unstable/graphql.json"
    variables = {"name": name, "return_url": return_url, "trial_days": trial_days, "amount": price}
    data = {"query": ANNUAL_CHARGE_MUTATION, "variables": variables}
    response = requests.post(url, headers=headers, json=data, timeout=10)
    response.raise_for_status()
    content = response.json()
    _check_for_errors(content)

    return content["data"]["appSubscriptionCreate"]["confirmationUrl"]