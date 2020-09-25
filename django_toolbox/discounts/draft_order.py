import time
from typing import List, Tuple

from django.contrib.auth import get_user_model

from ..shopify_graphql import run_query
from .collections import LineItem, DraftOrderResponse
from .discount import get_discount


CREATE_DRAFT_ORDER_MUTATION = """
mutation createDraftOrder($input: DraftOrderInput!) {
  draftOrderCreate(input: $input) {
    draftOrder {
      legacyResourceId
      invoiceUrl
    }
    userErrors {
      field
      message
    }
  }
}
"""


AuthAppShopUser = get_user_model()


def transform_attributes(attributes: dict):
    if not hasattr(attributes, "items"):
        return
    return [
        {"key": name, "value": str(value)}
        for name, value in attributes.items()
        if value
    ]


def execute_create_draft_order(
    shop: AuthAppShopUser, variables: dict
) -> DraftOrderResponse:
    draft_order = run_query(
        shop.token, shop.myshopify_domain, CREATE_DRAFT_ORDER_MUTATION, variables
    )

    draft_order_create = draft_order["data"]["draftOrderCreate"]
    assert draft_order_create["draftOrder"], draft_order_create["userErrors"]
    draft_order_id = int(draft_order_create["draftOrder"]["legacyResourceId"])
    invoice_url = draft_order_create["draftOrder"]["invoiceUrl"]

    # FIXME: Waiting for Shopify to provide a way to tell us we need to wait before invoice is ready.
    time.sleep(0.5)

    return DraftOrderResponse(id=draft_order_id, invoice_url=invoice_url)


def create_draft_order(shop: AuthAppShopUser, data, get_offers_line_items):
    cart = data["cart"]
    discount_code = data.get("discount_code")
    discount = get_discount(shop, discount_code, cart)

    line_and_cart_items: List[Tuple[LineItem, dict]] = [
        (
            LineItem(
                quantity=cart_line["quantity"],
                variantId="gid://shopify/ProductVariant/{0}".format(
                    cart_line["variant_id"]
                ),
                customAttributes=transform_attributes(cart_line["properties"]),
                appliedDiscount=None,
            ),
            cart_line,
        )
        for cart_line in cart["items"]
    ]
    line_items = list(discount.apply_discount_to_line_items(line_and_cart_items))
    line_items += get_offers_line_items(shop, data)

    variables = {
        "input": {
            "lineItems": line_items,
            "tags": "candybox",
            "customAttributes": transform_attributes(cart["attributes"]),
            "appliedDiscount": discount.apply_all_items_discount(),
            "note": cart["note"],
            "shippingAddress": data.get("shippingAddress"),
        }
    }
    response = execute_create_draft_order(shop, variables)

    return response
