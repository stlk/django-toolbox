from django.conf import settings
from django.shortcuts import reverse
from django_toolbox.shopify_graphql import run_query
import shopify
from decimal import Decimal


ANNUAL_CHARGE_MUTATION = """
mutation AnnualSubscriptionCreate($name: String!, $return_url: URL!, $trial_days: Int!, $amount: Decimal!, $test: Boolean) {
  appSubscriptionCreate(
      name: $name,
      returnUrl: $return_url,
      trialDays: $trial_days,
      test: $test,
      lineItems: [{plan: {appRecurringPricingDetails: {price: {amount: $amount, currencyCode: USD}, interval: ANNUAL}}}]
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
"""

SUBSCRIPTION_QUERY = """
{
  appInstallation {
    activeSubscriptions {
      name
      trialDays
      lineItems {
        plan {
          pricingDetails {
            ... on AppRecurringPricing {
              interval
              price {
                amount
              }
            }
          }
        }
      }
    }
  }
}
"""

TWOPLACES = Decimal(10) ** -2


def get_subscription(shop):
    content = run_query(
        shop.token, shop.myshopify_domain, SUBSCRIPTION_QUERY, api_version="2020-07",
    )
    if content["data"]["appInstallation"]["activeSubscriptions"]:
        return content["data"]["appInstallation"]["activeSubscriptions"][0]


def calculate_subscription_pricing(subscription_node):
    details = subscription_node["lineItems"][0]["plan"]["pricingDetails"]
    interval = details["interval"]
    price = details["price"]["amount"]

    if interval == "ANNUAL":
        # we're at 80% of original price /80*100 calculates 100%
        annual_subscription_price = Decimal(price).quantize(TWOPLACES)
        monthly_subscription_price = Decimal(
            annual_subscription_price / 12 / 80 * 100
        ).quantize(TWOPLACES)
        annual_subscription_price_monthly = Decimal(
            annual_subscription_price / 12
        ).quantize(TWOPLACES)

    if interval == "EVERY_30_DAYS":
        monthly_subscription_price = Decimal(price).quantize(TWOPLACES)
        annual_subscription_price = Decimal(
            monthly_subscription_price * 80 / 100 * 12
        ).quantize(TWOPLACES)
        annual_subscription_price_monthly = Decimal(
            annual_subscription_price / 12
        ).quantize(TWOPLACES)

    return {
        "monthly_subscription_price": monthly_subscription_price,
        "annual_subscription_price": annual_subscription_price,
        "annual_subscription_price_monthly": annual_subscription_price_monthly,
        "interval": interval,
    }


def build_return_url(request, shop):
    return request.build_absolute_uri(
        reverse("billing:activate-charge")
        + f"?myshopify_domain={shop.myshopify_domain}"
    )


def create_charge(request, shop: shopify.Shop):
    price, trial_days, name = settings.BILLING_FUNCTION(shop)

    return shopify.RecurringApplicationCharge.create(
        {
            "name": name,
            "price": price,
            "return_url": build_return_url(request, request.user),
            "trial_days": trial_days,
            "test": settings.SHOPIFY_APP_TEST_CHARGE,
        }
    )


def create_annual_charge(request, shop):
    subscription_node = get_subscription(shop)
    subscription_pricing = calculate_subscription_pricing(subscription_node)

    annual_subscription_price = subscription_pricing["annual_subscription_price"]
    name = subscription_node["name"]
    content = run_query(
        shop.token,
        shop.myshopify_domain,
        ANNUAL_CHARGE_MUTATION,
        variables={
            "name": f"{name} - Annual",
            "return_url": build_return_url(request, shop),
            "trial_days": 0,
            "amount": str(annual_subscription_price),
            "test": settings.SHOPIFY_APP_TEST_CHARGE,
        },
        api_version="2020-07",
    )

    return content["data"]["appSubscriptionCreate"]["confirmationUrl"]
