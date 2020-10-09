from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import get_user_model
from django.http import HttpResponse
from django.shortcuts import render, reverse
from django.utils.decorators import method_decorator
from django.views.generic.base import View
from django.views.generic.edit import FormView

from .forms import ConfigurationForm
from .shopify_scripts import has_scripts, create_script, delete_script
from .theme_update import (
    check_and_modify_theme_file,
    find_config_asset,
    get_main_theme_id,
    get_snippet,
    get_theme_liquid_content,
    set_snippet,
    update_config_asset,
    update_snippet,
)


@method_decorator(staff_member_required, name="dispatch")
class ThemeLiquidView(View):
    def get(self, request):
        user = get_user_model()
        shop = user.objects.get(id=self.request.GET.get("shop_id"))
        with shop.session:
            try:
                theme_liquid = get_theme_liquid_content(get_main_theme_id())
            except Exception as e:
                theme_liquid = str(e)

        return HttpResponse(theme_liquid, content_type="text/plain")


@method_decorator(staff_member_required, name="dispatch")
class ManageScriptView(View):
    template_name = "backoffice/manage-script.html"

    def get(self, request, shop_id):
        user = get_user_model()
        shop = user.objects.get(id=shop_id)
        with shop.session:
            try:
                snippet = get_snippet()
            except Exception as e:
                snippet = str(e)

        return render(
            request,
            self.template_name,
            {
                "shop_id": shop_id,
                "snippet": snippet,
                "script_installed": has_scripts(shop),
            },
        )

    def post(self, request, shop_id):
        user = get_user_model()
        shop = user.objects.get(id=shop_id)
        snippet = ""

        try:
            if "_clear" in request.POST:
                with shop.session:
                    main_theme_id = get_main_theme_id()
                    snippet = set_snippet(main_theme_id, "")
                messages.add_message(request, messages.INFO, "Snippet was cleared.")

            elif "_document_listener" in request.POST:
                with shop.session:
                    main_theme_id = get_main_theme_id()
                    check_and_modify_theme_file(main_theme_id)
                    snippet = update_snippet(
                        main_theme_id, enable_document_listener=True
                    )
                messages.add_message(
                    request,
                    messages.INFO,
                    "Snippet with document listener was inserted.",
                )

            elif "_cloning" in request.POST:
                with shop.session:
                    main_theme_id = get_main_theme_id()
                    check_and_modify_theme_file(main_theme_id)
                    snippet = update_snippet(
                        main_theme_id, enable_document_listener=False
                    )
                messages.add_message(
                    request, messages.INFO, "Snippet with button cloning was inserted."
                )

            elif "_activate_script_tag" in request.POST:
                try:
                    create_script(shop)
                    messages.add_message(request, messages.INFO, "Script activated.")
                except Exception as e:
                    messages.add_message(
                        request, messages.ERROR, f"Script activation failed: {e}"
                    )

            elif "_deactivate_script_tag" in request.POST:
                delete_script(shop)
                messages.add_message(request, messages.INFO, "Script deactivated.")

        except Exception as e:
            messages.add_message(request, messages.ERROR, f"Shopify call failed: {e}")

        return render(
            request,
            self.template_name,
            {
                "shop_id": shop_id,
                "script_installed": has_scripts(shop),
                "snippet": snippet,
            },
        )


@method_decorator(staff_member_required, name="dispatch")
class ConfigurationView(FormView):
    template_name = "backoffice/configuration.html"
    form_class = ConfigurationForm

    def form_valid(self, form):
        user = get_user_model()
        shop = user.objects.get(id=self.request.GET.get("shop_id"))
        with shop.session:
            try:
                config_asset = update_config_asset(
                    get_main_theme_id(), form.data["text"]
                )
                messages.add_message(
                    self.request,
                    messages.INFO,
                    "Configuration has been successfully updated.",
                )
            except Exception as e:
                messages.add_message(self.request, messages.ERROR, str(e))
        return super(ConfigurationView, self).form_valid(form)

    def get_success_url(self):
        shop_id = self.request.GET.get("shop_id")
        return reverse("backoffice-common:manage-script", kwargs={"shop_id": shop_id})

    def get_initial(self):
        initial = {}
        user = get_user_model()
        shop = user.objects.get(id=self.request.GET.get("shop_id"))
        with shop.session:
            try:
                config_asset = find_config_asset(get_main_theme_id())
                initial = {"text": config_asset.value}
            except Exception as e:
                messages.add_message(self.request, messages.ERROR, str(e))
        return initial
