from django.contrib.auth import logout as log_out
from django.http import HttpResponseRedirect

from social_django.views import disconnect as social_disconnect


def disconnect(request):
    response = social_disconnect(request, "auth0")
    log_out(request)
    return response


def logout(request):
    log_out(request)
    return HttpResponseRedirect("/admin")


def override_login(request):
    """
    Allow to see merchant's analytics for staff user.
    """
    if request.user.is_staff:
        request.session["shop_id"] = request.GET["shop_id"]

    return HttpResponseRedirect("/dashboard/analytics?disable_redirect=1")
