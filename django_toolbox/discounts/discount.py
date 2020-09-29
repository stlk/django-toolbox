from itertools import chain
from pathlib import Path
from typing import List, Optional

from django.contrib.auth import get_user_model

from ..shopify_graphql import GraphQLResponseError, run_query
from .collections import (
    CartLine,
    LineItem,
    covered_collections_query,
    get_items_in_collections,
    is_item_covered,
)
from django_toolbox.discounts import discount


AuthAppShopUser = get_user_model()


def flatten(list_of_lists):
    "Flatten one level of nesting"
    return chain.from_iterable(list_of_lists)


class Discount:
    shop: AuthAppShopUser

    def apply_discount_to_line_items(self, line_and_cart_items):
        for line_item, cart_item in line_and_cart_items:
            line_item["appliedDiscount"] = self.get_line_item_applied_discount(
                cart_item
            )
            yield line_item

    def get_line_item_applied_discount(self, cart_line):
        raise NotImplemented()

    def apply_all_items_discount(self):
        raise NotImplemented()


class NoDiscount(Discount):
    def get_line_item_applied_discount(self, cart_line):
        return None

    def apply_all_items_discount(self):
        return None


class DiscountBuyXGetY(Discount):
    discount_value: float = 0.00
    discount_code: str
    discount_quantity: int = 0
    customer_gets_items: List[int]
    customer_gets_variants: List[int]
    customer_gets_collections: List[int]
    customer_buys_min_amount_requirement: Optional[float] = 0.00
    customer_buys_min_quantity_requirement: Optional[int] = 0
    customer_buys_items: List[int]
    customer_buys_variants: List[int]
    customer_buys_collections: List[int]

    def __init__(self, code_discount_node, discount_code: str) -> None:
        """
        List default don't work as expected. They have to be set inside the constructor.
        """
        self.discount_code = discount_code
        self.customer_gets_items = []
        self.customer_gets_variants = []
        self.customer_gets_collections = []
        self.customer_buys_items = []
        self.customer_buys_variants = []
        self.customer_buys_collections = []

        # discount for specific items, specific variants or specific collection
        customer_gets_items = code_discount_node["codeDiscount"]["customerGets"][
            "items"
        ]
        customer_gets_value_type_node = code_discount_node["codeDiscount"][
            "customerGets"
        ]["value"]

        if "products" in customer_gets_items:
            self.customer_gets_items = get_items_ids(customer_gets_items, "products")
        if "productVariants" in customer_gets_items:
            self.customer_gets_variants = get_items_ids(
                customer_gets_items, "productVariants"
            )
        if "collections" in customer_gets_items:
            self.customer_gets_collections = get_items_ids(
                customer_gets_items, "collections"
            )
        self.discount_quantity = customer_gets_value_type_node["quantity"]["quantity"]
        self.discount_value = customer_gets_value_type_node["effect"]["percentage"]

        # target specific items, specific variants or specific collection
        customer_buys_items = code_discount_node["codeDiscount"]["customerBuys"][
            "items"
        ]
        customer_buys_value_type_node = code_discount_node["codeDiscount"][
            "customerBuys"
        ]["value"]

        if "products" in customer_buys_items:
            self.customer_buys_items = get_items_ids(customer_buys_items, "products")
        if "productVariants" in customer_buys_items:
            self.customer_buys_variants = get_items_ids(
                customer_buys_items, "productVariants"
            )
        if "collections" in customer_buys_items:
            self.customer_buys_collections = get_items_ids(
                customer_buys_items, "collections"
            )

        self.customer_buys_min_amount_requirement = customer_buys_value_type_node.get(
            "amount"
        )
        self.customer_buys_min_quantity_requirement = customer_buys_value_type_node.get(
            "quantity"
        )

    @classmethod
    def load(
        cls, shop: AuthAppShopUser, discount_code: str, code_discount_node, cart
    ) -> Discount:
        discount = cls(code_discount_node, discount_code)
        discount.shop = shop

        products_in_collections = covered_collections_query(
            shop,
            discount.customer_gets_collections + discount.customer_buys_collections,
            [item["product_id"] for item in cart["items"]],
        )

        customer_gets_products_in_collections = [
            products_in_collections[f"_{customer_gets_collection}"]
            for customer_gets_collection in discount.customer_gets_collections
        ]
        items_to_apply_discount = [
            item["product_id"]
            for item in cart["items"]
            if is_item_covered(
                customer_gets_products_in_collections, item["product_id"]
            )
        ]
        discount.customer_gets_items += items_to_apply_discount

        if not discount.enforce_amount_requirement(
            cart, products_in_collections
        ) or not discount.enforce_quantity_requirement(cart, products_in_collections):
            return NoDiscount()

        return discount

    def enforce_amount_requirement(self, cart, products_in_collections):
        if self.customer_buys_min_amount_requirement:
            items_in_collection = []
            if self.customer_buys_collections:
                customer_buys_products_in_collections = [
                    products_in_collections[f"_{customer_buys_collection}"]
                    for customer_buys_collection in self.customer_buys_collections
                ]
                items_in_collection = [
                    item["product_id"]
                    for item in cart["items"]
                    if is_item_covered(
                        customer_buys_products_in_collections, item["product_id"]
                    )
                ]
            if (
                self.customer_buys_items
                or self.customer_buys_variants
                or self.customer_buys_collections
            ):
                amount = sum(
                    [
                        item["line_price"]
                        for item in cart["items"]
                        if item["product_id"] in self.customer_buys_items
                        or item["variant_id"] in self.customer_buys_variants
                        or item["product_id"] in items_in_collection
                    ]
                )
                if amount >= float(self.customer_buys_min_amount_requirement):
                    return True
        else:
            return True

    def enforce_quantity_requirement(self, cart, products_in_collections):
        if self.customer_buys_min_quantity_requirement:
            items_in_collection = []
            if self.customer_buys_collections:
                customer_buys_products_in_collections = [
                    products_in_collections[f"_{customer_buys_collection}"]
                    for customer_buys_collection in self.customer_buys_collections
                ]
                items_in_collection = [
                    item["product_id"]
                    for item in cart["items"]
                    if is_item_covered(
                        customer_buys_products_in_collections, item["product_id"]
                    )
                ]
            if (
                self.customer_buys_items
                or self.customer_buys_variants
                or self.customer_buys_collections
            ):
                quantity = sum(
                    [
                        item["quantity"]
                        for item in cart["items"]
                        if item["product_id"] in self.customer_buys_items
                        or item["variant_id"] in self.customer_buys_variants
                        or item["product_id"] in items_in_collection
                    ]
                )
                if quantity >= int(self.customer_buys_min_quantity_requirement):
                    return True
        else:
            return True

    def apply_discount_to_line_item(self, line_item: LineItem, cart_line: CartLine):
        if not self.customer_gets_items and not self.customer_gets_variants:
            yield line_item
            return

        if (cart_line["product_id"] not in self.customer_gets_items) and (
            cart_line["variant_id"] not in self.customer_gets_variants
        ):
            yield line_item
            return

        if int(self.discount_quantity) > cart_line["quantity"]:
            yield line_item
            return

        # Shopify returns discount as 0 - 1 but draft order discount application expects values 0 - 100
        discount_value = self.discount_value * 100

        if int(self.discount_quantity) < cart_line["quantity"]:
            yield LineItem(
                quantity=cart_line["quantity"] - int(self.discount_quantity),
                variantId=line_item["variantId"],
                customAttributes=line_item["customAttributes"],
                appliedDiscount=None,
            )

        line_item["quantity"] = int(self.discount_quantity)
        line_item["appliedDiscount"] = {
            "title": self.discount_code,
            "value": discount_value,
            "valueType": "PERCENTAGE",
        }
        yield line_item

    def apply_discount_to_line_items(self, line_and_cart_items):
        return flatten(
            [
                list(self.apply_discount_to_line_item(line_item, cart_item))
                for line_item, cart_item in line_and_cart_items
            ]
        )

    def apply_all_items_discount(self):
        return None


class DiscountBasic(Discount):
    all_items_discount: bool = False
    applies_on_each_item: bool
    discount_value_type: str
    discount_value: float
    discount_code: str
    min_amount_requirement: Optional[float] = 0.00
    min_quantity_requirement: Optional[int] = 0
    customer_gets_items: List[int]
    customer_gets_variants: List[int]
    customer_gets_collections: List[int]
    discount_items_count: Optional[int]

    def __init__(self, code_discount_node, discount_code: str) -> None:
        """
        List default don't work as expected. They have to be set inside the constructor.
        """
        self.discount_code = discount_code
        self.customer_gets_items = []
        self.customer_gets_variants = []
        self.customer_gets_collections = []

        customer_gets_items = code_discount_node["codeDiscount"]["customerGets"][
            "items"
        ]

        # discount for all items, specific items, specific variants or specific collection
        customer_gets_value_type_node = code_discount_node["codeDiscount"][
            "customerGets"
        ]["value"]
        self.applies_on_each_item = customer_gets_value_type_node.get(
            "appliesOnEachItem", False
        )

        if "allItems" in customer_gets_items:
            self.all_items_discount = customer_gets_items["allItems"]
        if "products" in customer_gets_items:
            self.customer_gets_items = get_items_ids(customer_gets_items, "products")
        if "productVariants" in customer_gets_items:
            self.customer_gets_variants = get_items_ids(
                customer_gets_items, "productVariants"
            )
        if "collections" in customer_gets_items:
            self.customer_gets_collections = get_items_ids(
                customer_gets_items, "collections"
            )

        # fixed amount or percentage discount
        if "percentage" in customer_gets_value_type_node:
            self.discount_value = float(customer_gets_value_type_node["percentage"])
            self.discount_value_type = "PERCENTAGE"
        if "amount" in customer_gets_value_type_node:
            self.discount_value = float(
                customer_gets_value_type_node["amount"]["amount"]
            )
            self.discount_value_type = "FIXED_AMOUNT"

        # minimum requirements
        min_requirements_node = code_discount_node["codeDiscount"].get(
            "minimumRequirement"
        )

        if min_requirements_node:
            if "greaterThanOrEqualToSubtotal" in min_requirements_node:
                self.min_amount_requirement = float(
                    min_requirements_node["greaterThanOrEqualToSubtotal"]["amount"]
                )
            if "greaterThanOrEqualToQuantity" in min_requirements_node:
                self.min_quantity_requirement = int(
                    min_requirements_node["greaterThanOrEqualToQuantity"]
                )

    @classmethod
    def load(
        cls, shop: AuthAppShopUser, discount_code: str, code_discount_node, cart
    ) -> Discount:
        discount = cls(code_discount_node, discount_code)

        items_to_apply_discount = get_items_in_collections(
            shop,
            discount.customer_gets_collections,
            [item["product_id"] for item in cart["items"]],
        )
        discount.customer_gets_items += items_to_apply_discount

        if not discount.enforce_amount_requirement(
            cart
        ) or not discount.enforce_quantity_requirement(cart):
            return NoDiscount()

        if discount.customer_gets_items:
            discount.discount_items_count = sum(
                [
                    item["quantity"]
                    for item in cart["items"]
                    if item["product_id"] in discount.customer_gets_items
                ]
            )

        if discount.customer_gets_variants:
            discount.discount_items_count = sum(
                [
                    item["quantity"]
                    for item in cart["items"]
                    if item["variant_id"] in discount.customer_gets_variants
                ]
            )
        return discount

    def enforce_amount_requirement(self, cart):
        if self.min_amount_requirement:
            if self.all_items_discount:
                if cart["total_price"] >= self.min_amount_requirement * 100:
                    return True
            if self.customer_gets_items or self.customer_gets_variants:
                amount = sum(
                    [
                        item["line_price"]
                        for item in cart["items"]
                        if item["product_id"] in self.customer_gets_items
                        or item["variant_id"] in self.customer_gets_variants
                    ]
                )
                if amount >= self.min_amount_requirement:
                    return True
        else:
            return True

    def enforce_quantity_requirement(self, cart):
        if self.min_quantity_requirement:
            if self.all_items_discount:
                if cart["item_count"] >= self.min_quantity_requirement:
                    return True
            if self.customer_gets_items or self.customer_gets_variants:
                quantity = sum(
                    [
                        item["quantity"]
                        for item in cart["items"]
                        if item["product_id"] in self.customer_gets_items
                        or item["variant_id"] in self.customer_gets_variants
                    ]
                )
                if quantity >= self.min_quantity_requirement:
                    return True
        else:
            return True

    def apply_all_items_discount(self):
        if not self.all_items_discount:
            return None

        discount_value = self.discount_value

        if self.discount_value_type == "PERCENTAGE":
            # Shopify returns discount as 0 - 1 but draft order discount application expects values 0 - 100
            discount_value = self.discount_value * 100

        return {
            "title": self.discount_code,
            "value": discount_value,
            "valueType": self.discount_value_type,
        }

    def get_line_item_applied_discount(self, cart_line):
        if not self.customer_gets_items and not self.customer_gets_variants:
            return None

        if (cart_line["product_id"] not in self.customer_gets_items) and (
            cart_line["variant_id"] not in self.customer_gets_variants
        ):
            return None

        # calculate the discount value
        if self.discount_value_type == "PERCENTAGE":
            # Shopify returns discount as 0 - 1 but draft order discount application expects values 0 - 100
            discount_value = self.discount_value * 100

        elif self.discount_value_type == "FIXED_AMOUNT":
            discount_value = self.discount_value

            if not self.applies_on_each_item:
                # count discount value for each item available for discount in cart
                # Applied discount value can have at most 2 digits after decimal point
                discount_value = round(
                    self.discount_value / self.discount_items_count, 2
                )

        else:
            return None

        return {
            "title": self.discount_code,
            "value": discount_value,
            "valueType": self.discount_value_type,
        }


def get_items_ids(items_node: dict, item_node_key: str):
    return [
        int(node["node"]["id"].split("/")[-1])
        for node in items_node[item_node_key]["edges"]
    ]


def get_discount_node(shop: AuthAppShopUser, discount_code: str):
    # Crude security measure to prevent GraphQL injection
    discount_code = discount_code.replace('"', "").replace("{", "")
    discount_query_file = Path(__file__).parent / "discount.graphql"

    try:
        content = run_query(
            shop.token,
            shop.myshopify_domain,
            discount_query_file.read_text(),
            {"code": discount_code},
        )
        return content["data"]["codeDiscountNodeByCode"]
    except GraphQLResponseError as e:
        if not [error for error in e.errors if "Parse error" in error["message"]]:
            raise


def get_discount(shop: AuthAppShopUser, discount_code: str, cart):
    if not discount_code or not shop.settings.discounts_enabled:
        return NoDiscount()

    code_discount_node = get_discount_node(shop, discount_code)

    if not code_discount_node or not code_discount_node["codeDiscount"]:
        return NoDiscount()

    discount_type = code_discount_node["codeDiscount"]["__typename"]
    discount: Discount = NoDiscount()

    if discount_type == "DiscountCodeBasic":
        discount = DiscountBasic.load(shop, discount_code, code_discount_node, cart)

    if discount_type == "DiscountCodeBxgy":
        discount = DiscountBuyXGetY.load(shop, discount_code, code_discount_node, cart)

    return discount


def validate_discount_code(shop: AuthAppShopUser, discount_code: str):
    code_discount_node = get_discount_node(shop, discount_code)

    if not code_discount_node:
        return {"active": False, "reason": "discount_not_found"}

    code_discount = code_discount_node["codeDiscount"]

    if not code_discount:
        return {"active": False, "reason": "discount_not_found"}

    if code_discount.get("usageLimit") and (
        code_discount["asyncUsageCount"] >= code_discount["usageLimit"]
    ):
        return {"active": False, "reason": "usage_limit_reached"}

    if code_discount_node["codeDiscount"]["__typename"] == "DiscountCodeFreeShipping":
        return {"active": False, "reason": "free_shipping_not_supported"}

    return {
        "active": code_discount["status"] == "ACTIVE",
    }
