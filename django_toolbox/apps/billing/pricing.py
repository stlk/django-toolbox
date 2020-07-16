from django.conf import settings
from django.shortcuts import reverse
from django_toolbox.shopify_graphql import _check_for_errors, run_query
import shopify


ANNUAL_CHARGE_MUTATION = '''mutation AnnualSubscriptionCreate($name: String!, $return_url: URL!, $trial_days: Int!, $amount: Decimal!){
    appSubscriptionCreate(
        name: $name
        returnUrl: $return_url
        trialDays: $trial_days
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

SUBSCRIPTION_QUERY = '''
{
  appInstallation {
    activeSubscriptions {
      name
      status
      currentPeriodEnd
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
'''


def get_subscription(shop):
    content = run_query(
            shop.token,
            shop.myshopify_domain,
            SUBSCRIPTION_QUERY,
            api_version="2020-07",
        )
    _check_for_errors(content)
    if content["data"]["appInstallation"]["activeSubscriptions"]:
        return content["data"]["appInstallation"]["activeSubscriptions"][0]


def create_charge(request, shop):
    price, trial_days, name = settings.BILLING_FUNCTION(shop)
    if request.session.get("promo_code") == "carson":
        name = f"{name} - Carson Promo"
        price = price * 0.75

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
    subscription_node = get_subscription(shop)

    if subscription_node:
        price = subscription_node["lineItems"][0]["plan"]["pricingDetails"]["price"]["amount"]
        trial_days = subscription_node["trialDays"]
        name = subscription_node["name"]
        return_url = request.build_absolute_uri(reverse("billing:activate-charge"))
        content = run_query(
            shop.token,
            shop.myshopify_domain,
            ANNUAL_CHARGE_MUTATION,
            variables={"name": f"{name} - Annual", "return_url": return_url, "trial_days": trial_days, "amount": price},
            api_version="2020-07",
        )

        _check_for_errors(content)

        return content["data"]["appSubscriptionCreate"]["confirmationUrl"]
