import shopify
from django.shortcuts import render, redirect, reverse
from django.views.generic.base import View
from django.views.generic.edit import FormView
from django.conf import settings
from django.contrib.auth.mixins import PermissionRequiredMixin
from .mixins import ShopifyLoginRequiredMixin
from .signals import app_installed
from . import pricing
from .forms import DiscountTokenForm


class CreateChargeView(ShopifyLoginRequiredMixin, View):
    def create_charge(self, request):
        charge = pricing.create_charge(request)

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


class DiscountView(View):

    template_name = "billing/discount.html"

    def get(self, request, token):
        token = pricing.save_discount_to_cookie(token, request)
        try:
            assert token["shop"] == request.user.myshopify_domain
            with request.user.session:
                active_subscription = shopify.RecurringApplicationCharge.current()
        except:
            active_subscription = False

        return render(
            request,
            self.template_name,
            {
                "token": token,
                "login_url": settings.LOGIN_URL,
                "active_subscription": active_subscription,
            },
        )

    def post(self, request, token):
        with request.user.session:
            shopify.RecurringApplicationCharge.current().destroy()

        return redirect("billing:create-charge")


class GenerateDiscountView(PermissionRequiredMixin, FormView):
    permission_required = "is_staff"
    form_class = DiscountTokenForm
    template_name = "billing/generate-discount.html"

    def form_valid(self, form):
        token = pricing.generate_token(form.cleaned_data)
        return render(
            self.request,
            self.template_name,
            {
                "token": self.request.build_absolute_uri(
                    reverse("billing:discount", args=(token,))
                )
            },
        )
