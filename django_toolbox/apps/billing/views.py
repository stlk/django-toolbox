import shopify
from django.shortcuts import render, redirect, reverse
from django.views.generic.base import View
from django.views.generic.edit import FormView
from django.conf import settings
from django.contrib.auth.mixins import PermissionRequiredMixin
from .mixins import ShopifyLoginRequiredMixin
from . import pricing


class CreateChargeView(ShopifyLoginRequiredMixin, View):
    def set_currency(self, user):
        if hasattr(user, "currency"):
            user.currency = self.shop.currency
            user.save(update_fields=["currency"])

    def create_charge(self, request):
        charge = pricing.create_charge(request, self.shop)

        return render(
            request, "billing/redirect.html", {"redirect": charge.confirmation_url}
        )

    def should_charge(self):
        """
        Charge only when shop is on paid plan.
        """

        return (
            settings.SHOPIFY_APP_TEST_CHARGE
            or not self.shop.plan_name in ["affiliate", "staff_business", "trial"]
        ) and not shopify.RecurringApplicationCharge.current()

    def get(self, request):
        with request.user.session:
            self.set_currency(request.user)
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
                return redirect(settings.BILLING_REDIRECT_URL)

        return render(
            request,
            self.template_name,
            {"charge": charge.attributes, "shop": self.shop},
        )
