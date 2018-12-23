import time
import logging

import pyactiveresource.connection
from shopify.base import ShopifyConnection

logger = logging.getLogger("django.shopify")

RATIO_THRESHOLD = 0.8
LONG_REQUEST_THRESHOLD = 1000


def _check_throttle_limits(response):
    try:
        call_limit = response.headers.get("X-Shopify-Shop-Api-Call-Limit")
        currently_used, maximum_available = map(int, call_limit.split("/"))
        usage_ratio = currently_used / maximum_available
        if usage_ratio > RATIO_THRESHOLD:
            logger.warning(
                f"ShopifyConnection exceeded {RATIO_THRESHOLD * 100}% notification limit. URL: {response.response.url}, call limit: {call_limit}"
            )
    except:
        logger.exception("ShopifyConnection limit check failed.")


def patch_shopify_with_limits():
    func = ShopifyConnection._open

    def patched_open(self, *args, **kwargs):
        start = time.time()
        while True:
            try:
                response = func(self, *args, **kwargs)
                _check_throttle_limits(response)
                duration = time.time() - start
                duration_ms = int(round(duration * 1000))
                if duration_ms > LONG_REQUEST_THRESHOLD:
                    logger.warning(f"Long request. {args} duration_ms: {duration_ms}")
                else:
                    logger.info(f"{args} duration_ms: {duration_ms}")
                return response

            except pyactiveresource.connection.ClientError as e:
                if e.response.code == 429:
                    retry_after = float(e.response.headers.get("Retry-After", 2))
                    logger.error(
                        f"Service exceeds Shopify API call limit, will retry to send request in {retry_after} seconds."
                    )
                    time.sleep(retry_after)
                else:
                    raise

    ShopifyConnection._open = patched_open


patch_shopify_with_limits()
