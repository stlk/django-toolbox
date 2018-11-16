import datetime
import jwt
import shopify
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.conf import settings
from django.shortcuts import reverse


def generate_token(payload):
    payload["generated"] = timezone.now().isoformat()
    return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256").decode("utf-8")


def decode_token(token):
    return jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])


def is_token_valid(decoded_token: dict):
    return (
        parse_datetime(decoded_token["generated"]) + datetime.timedelta(days=31)
        > timezone.now()
    )


def save_discount_to_cookie(token, request):
    try:
        decoded_token = decode_token(token)
        assert is_token_valid(decoded_token)
    except:
        return

    request.session["discount_token"] = token
    return decoded_token


def get_price_and_trial_days(request):
    try:
        token = request.session["discount_token"]
        decoded_token = decode_token(token)
        assert is_token_valid(decoded_token)
        return (decoded_token["price"], decoded_token["trial_days"])
    except:
        return (settings.BILLING_PRICE, settings.BILLING_TRIAL_DAYS)


def create_charge(request):
    price, trial_days = get_price_and_trial_days(request)
    return shopify.RecurringApplicationCharge.create(
        {
            "name": settings.BILLING_CHARGE_NAME,
            "price": price,
            "return_url": request.build_absolute_uri(
                reverse("billing:activate-charge")
            ),
            "trial_days": trial_days,
            "test": settings.SHOPIFY_APP_TEST_CHARGE,
        }
    )
