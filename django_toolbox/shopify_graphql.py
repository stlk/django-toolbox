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


def _get_query_meta_data(content):
    try:
        query_id = list(content["data"].keys())[0]
        requested_query_cost = content["extensions"]["cost"]["requestedQueryCost"]
        actual_query_cost = content["extensions"]["cost"]["actualQueryCost"]
        currently_available = content["extensions"]["cost"]["throttleStatus"][
            "currentlyAvailable"
        ]
        return {
            "query_id": query_id,
            "requested_query_cost": requested_query_cost,
            "actual_query_cost": actual_query_cost,
            "currently_available": currently_available,
        }
    except (KeyError, IndexError):
        return None


def _run_query(
    token: str,
    myshopify_domain: str,
    query: str,
    variables: dict = None,
    api_version: str = settings.SHOPIFY_APP_API_VERSION,
):
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


def run_query(
    token: str,
    myshopify_domain: str,
    query: str,
    variables: dict = None,
    api_version: str = settings.SHOPIFY_APP_API_VERSION,
):
    retry_count = 0
    while True:
        try:
            with elasticapm.capture_span(
                f"GraphQL:  {query[:50]}...", span_type="graphql", leaf=True
            ) as span:
                content = _run_query(
                    token, myshopify_domain, query, variables, api_version
                )
                if span:
                    meta_data = _get_query_meta_data(content)
                    if meta_data:
                        span.labels = {
                            "query_id": meta_data["query_id"],
                            "requested_query_cost": meta_data["requested_query_cost"],
                            "actual_query_cost": meta_data["actual_query_cost"],
                            "currently_available": meta_data["currently_available"],
                        }

                return content
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
