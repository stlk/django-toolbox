import shopify
from django.conf import settings
from django.shortcuts import reverse


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
