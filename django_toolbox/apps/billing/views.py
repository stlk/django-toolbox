import shopify
from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import get_user_model
from django.shortcuts import redirect, render, reverse
from django.utils.decorators import method_decorator
from django.views.generic.base import View
from django.views.generic.edit import FormView
from pyactiveresource.connection import ResourceNotFound, ResourceInvalid

from . import pricing
from .forms import RecurringApplicationChargeForm
from .mixins import ShopifyLoginRequiredMixin


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
            settings.BILLING_FUNCTION
            and (
                settings.SHOPIFY_APP_TEST_CHARGE
                or not self.shop.plan_name
                in ["partner_test", "affiliate", "staff_business", "trial"]
            )
            and not shopify.RecurringApplicationCharge.current()
        )

    def get(self, request):
        with request.user.session:
            self.set_currency(request.user)
            if self.should_charge():
                return self.create_charge(request)

        return redirect(settings.BILLING_REDIRECT_URL)


class CreateAnnualChargeView(ShopifyLoginRequiredMixin, View):
    def get(self, request):
        confirmation_url = pricing.create_annual_charge(request, request.user)

        return render(request, "billing/redirect.html", {"redirect": confirmation_url})


class ActivateChargeView(ShopifyLoginRequiredMixin, View):

    template_name = "billing/charge-result.html"

    def get(self, request):
        with request.user.session:
            try:
                charge = shopify.RecurringApplicationCharge.find(
                    request.GET["charge_id"]
                )
                if charge.status == "accepted":
                    charge.activate()
                    return redirect(settings.BILLING_REDIRECT_URL)
                if charge.status == "active":
                    return redirect(settings.BILLING_REDIRECT_URL)
            except (ResourceNotFound, ResourceInvalid):
                pass

        return render(request, self.template_name, {"shop": self.shop})


class PromoCodeView(View):
    def get(self, request, code):
        request.session["promo_code"] = code
        return redirect(reverse("billing:create-charge"))


@method_decorator(staff_member_required, name="dispatch")
class GenerateChargeView(FormView):
    form_class = RecurringApplicationChargeForm
    template_name = "billing/generate-charge.html"

    def get_initial(self):
        shop = get_user_model().objects.get(id=self.request.GET.get("shop_id"))
        with shop.session:
            try:
                charge = shopify.RecurringApplicationCharge.current()
                if not charge:
                    return {
                        "shop": shop.myshopify_domain,
                        "name": "this shop has no active charge",
                    }
            except:
                return {"shop": "error while getting current charge"}
        return {
            "shop": shop.myshopify_domain,
            "name": charge.name,
            "price": charge.price,
            "trial_days": charge.trial_days,
        }

    def form_valid(self, form):
        data = form.cleaned_data
        shop = get_user_model().objects.get(myshopify_domain=data["shop"])
        with shop.session:
            charge = shopify.RecurringApplicationCharge.create(
                {
                    "name": data["name"],
                    "price": str(data["price"]),
                    "return_url": self.request.build_absolute_uri(
                        reverse("billing:activate-charge")
                    ),
                    "trial_days": data["trial_days"],
                    "test": settings.SHOPIFY_APP_TEST_CHARGE,
                }
            )
            return render(
                self.request,
                self.template_name,
                {"confirmation_url": charge.confirmation_url},
            )
