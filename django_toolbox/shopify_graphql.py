import logging
import time

import elasticapm
import requests

from django.conf import settings

logger = logging.getLogger("django.shopify")


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


def _run_query(token: str, myshopify_domain: str, query: str, variables: dict = None, api_version: str = settings.SHOPIFY_APP_API_VERSION):
    headers = {
        "X-Shopify-Access-Token": token,
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    url = f"https://{myshopify_domain}/admin/api/{api_version}/graphql.json"

    data = {"query": query, "variables": variables}

    response = requests.post(url, headers=headers, json=data, timeout=10)
    response.raise_for_status()
    content = response.json()
    _check_for_errors(content)
    _check_throttle_limits(
        content,
        f"GraphQL query exceeded notification limit. shop: {myshopify_domain}, query: {query}",
    )
    return content


def run_query(*args, **kwargs):
    retry_count = 0
    while True:
        try:
            return _run_query(*args, **kwargs)
        except GraphQLResponseError as e:
            if [error for error in e.errors if error["message"] == "Throttled"]:
                if retry_count == 2:
                    raise
                retry_count += 1

                retry_after = 1
                logger.warning(
                    f"Service exceeds Shopify API call limit, will retry to send request in {retry_after} seconds."
                )
                with elasticapm.capture_span("GraphQL Throttled"):
                    time.sleep(retry_after)
            else:
                raise
