import time
import logging
import requests

logger = logging.getLogger("django.shopify")

LONG_REQUEST_THRESHOLD = 1000


class GraphQLResponseError(Exception):
    def __init__(self, errors):
        self.errors = errors
        message = "".join([error["message"] for error in errors])
        super().__init__(self, message)


def _check_throttle_limits(content: dict, message: str):
    throttle_status = content["extensions"]["cost"]["throttleStatus"]
    usage_ratio = (
        throttle_status["currentlyAvailable"] / throttle_status["maximumAvailable"]
    )
    if usage_ratio < 0.5:
        logger.warning(message)


def _check_for_errors(content):
    errors = content.get("errors", None)
    if errors:
        raise GraphQLResponseError(errors)


def _run_query(token: str, myshopify_domain: str, query: str):
    headers = {"X-Shopify-Access-Token": token, "Content-Type": "application/graphql"}
    url = f"https://{myshopify_domain}/admin/api/graphql.json"

    response = requests.post(url, headers=headers, data=query, timeout=10)
    response.raise_for_status()
    content = response.json()
    _check_for_errors(content)
    _check_throttle_limits(
        content,
        f"GraphQL query exceeded notification limit. shop: {myshopify_domain}, query: {query}",
    )
    return content


def run_query(self, *args, **kwargs):
    start = time.time()
    while True:
        try:
            response = _run_query(self, *args, **kwargs)
            duration = time.time() - start
            duration_ms = int(round(duration * 1000))
            if duration_ms > LONG_REQUEST_THRESHOLD:
                logger.warning(f"Long request. {args} duration_ms: {duration_ms}")
            else:
                logger.info(f"{args} duration_ms: {duration_ms}")
            return response
        except GraphQLResponseError as e:
            if [error for error in e.errors if error["message"] == "Throttled"]:
                retry_after = 2
                logger.error(
                    f"Service exceeds Shopify API call limit, will retry to send request in {retry_after} seconds."
                )
                time.sleep(retry_after)
            else:
                raise
