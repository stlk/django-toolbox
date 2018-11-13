import shopify
from django.shortcuts import render, redirect, reverse
from django.views.generic.base import View
from django.conf import settings
from .mixins import ShopifyLoginRequiredMixin
from .signals import app_installed


class CreateChargeView(ShopifyLoginRequiredMixin, View):
    def create_charge(self, request):
        charge = shopify.RecurringApplicationCharge.create(
            {
                "name": settings.BILLING_CHARGE_NAME,
                "price": settings.BILLING_PRICE,
                "return_url": request.build_absolute_uri(
                    reverse("billing:activate-charge")
                ),
                "trial_days": settings.BILLING_TRIAL_DAYS,
                "test": settings.SHOPIFY_APP_TEST_CHARGE,
            }
        )

        return render(
            request, "billing/redirect.html", {"redirect": charge.confirmation_url}
        )

    def should_charge(self):
        """
        Charge only when shop is on paid plan.
        """

        return (
            settings.SHOPIFY_APP_TEST_CHARGE or self.shop.plan_name != "affiliate"
        ) and not shopify.RecurringApplicationCharge.current()

    def get(self, request):
        app_installed.send(sender=self.__class__, request=request)
        with request.user.session:
            if self.should_charge():
                return self.create_charge(request)

        return redirect(settings.BILLING_REDIRECT_URL)


class ActivateChargeView(ShopifyLoginRequiredMixin, View):

    template_name = "billing/charge-result.html"

    def get(self, request):
        with request.user.session:
            charge = shopify.RecurringApplicationCharge.find(request.GET["charge_id"])
            if charge.status == "accepted":
                charge.activate()

        return render(
            request,
            self.template_name,
            {"charge": charge.attributes, "shop": self.shop},
        )
