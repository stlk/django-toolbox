from django.contrib.auth import get_user_model


class OverrideLoginMixin(object):
    def dispatch(self, request, *args, **kwargs):
        shop_id = request.session.get("shop_id")
        if request.user.is_staff and shop_id:
            request.user = get_user_model().objects.get(id=shop_id)

        return super().dispatch(request, *args, **kwargs)
