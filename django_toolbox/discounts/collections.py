from typing import List, Optional, TypedDict, NamedTuple

from django.contrib.auth import get_user_model

from ..shopify_graphql import run_query


AuthAppShopUser = get_user_model()


class LineItem(TypedDict, total=False):
    quantity: int
    variantId: Optional[str]
    title: Optional[str]
    customAttributes: Optional[List[dict]]
    originalUnitPrice: Optional[str]
    appliedDiscount: Optional[dict]


class CartLine(TypedDict, total=False):
    id: int
    product_id: int
    variant_id: int
    quantity: int


class DraftOrderResponse(NamedTuple):
    id: int
    invoice_url: str


def get_items_in_collections(
    shop: AuthAppShopUser, spec_discount_collections: List[int], item_ids: List[int]
) -> list:
    if not spec_discount_collections:
        return []

    content = covered_collections_query(shop, spec_discount_collections, item_ids)
    items_in_collections = [
        item_id for item_id in item_ids if is_item_covered(content.values(), item_id)
    ]

    return items_in_collections


def covered_collections_query(
    shop: AuthAppShopUser, spec_discount_collections: List[int], item_ids: List[int]
) -> dict:
    if not spec_discount_collections:
        return {}

    products_query = "".join(
        [
            f"""_{item_id}:hasProduct(id: "gid://shopify/Product/{item_id}")"""
            for item_id in item_ids
        ]
    )
    collections_query = "".join(
        [
            f"""_{collection_id}:collection(id: "gid://shopify/Collection/{collection_id}") {{{products_query}}}"""
            for collection_id in spec_discount_collections
        ]
    )

    return run_query(shop.token, shop.myshopify_domain, f"{{{collections_query}}}")[
        "data"
    ]


def is_item_covered(collection_edges: List, product_id: int):
    return any(
        collection_edge[f"_{product_id}"]
        for collection_edge in collection_edges
        if collection_edge
    )


def get_covered_collections_with_items(
    shop: AuthAppShopUser, spec_discount_collections: List[int], product_ids: List[int]
):
    if not spec_discount_collections:
        return []

    content = covered_collections_query(shop, spec_discount_collections, product_ids)
    covered_collections = {
        int(col.replace("_", "")): [
            int(product_id.replace("_", ""))
            for product_id, is_in_collection in products.items()
            if is_in_collection
        ]
        for col, products in content.items()
        if is_collection_covered(products, product_ids)
    }

    return covered_collections


def is_collection_covered(collection_edges: List, item_ids: List):
    return any(
        collection_edges[f"_{item_id}"] for item_id in item_ids if collection_edges
    )
