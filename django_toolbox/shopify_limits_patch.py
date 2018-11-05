import time
import logging

import pyactiveresource.connection
from shopify.base import ShopifyConnection


def _check_throttle_limits(response):
    try:
        call_limit = response.headers.get("X-Shopify-Shop-Api-Call-Limit")
        currently_used, maximum_available = map(int, call_limit.split("/"))
        usage_ratio = currently_used / maximum_available
        if usage_ratio > 0.5:
            logging.warning(
                f"ShopifyConnection exceeded 50% notification limit. URL: {response.response.url}, call limit: {call_limit}"
            )
    except:
        logging.exception("ShopifyConnection limit check failed.")


def patch_shopify_with_limits():
    func = ShopifyConnection._open

    def patched_open(self, *args, **kwargs):
        while True:
            try:
                response = func(self, *args, **kwargs)
                _check_throttle_limits(response)
                return response

            except pyactiveresource.connection.ClientError as e:
                if e.response.code == 429:
                    retry_after = float(e.response.headers.get("Retry-After", 4))
                    logging.error(
                        f"Service exceeds Shopify API call limit, will retry to send request in {retry_after} seconds."
                    )
                    time.sleep(retry_after)
                else:
                    raise e

    ShopifyConnection._open = patched_open


patch_shopify_with_limits()
