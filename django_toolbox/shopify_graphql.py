import logging
import requests


def _check_throttle_limits(content: dict, message: str):
    throttle_status = content["extensions"]["cost"]["throttleStatus"]
    usage_ratio = (
        throttle_status["currentlyAvailable"] / throttle_status["maximumAvailable"]
    )
    if usage_ratio < 0.5:
        logging.warning(message)


def _check_for_errors(content):
    errors = content.get("errors", None)
    if errors:
        [logging.error(f"GraphQL: {error['message']}") for error in errors]
    return errors


def run_query(token: str, myshopify_domain: str, query: str):
    headers = {
        "X-Shopify-Access-Token": token,
        "Content-Type": "application/graphql",
    }
    url = f"https://{myshopify_domain}/admin/api/graphql.json"

    response = requests.post(url, headers=headers, data=query)
    response.raise_for_status()
    content = response.json()
    _check_throttle_limits(
        content,
        f"GraphQL query exceeded notification limit. shop: {myshopify_domain}, query: {query}",
    )
    return content
