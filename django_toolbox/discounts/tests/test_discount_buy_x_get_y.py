from django.conf import settings
import responses
import copy
from unittest.mock import patch
from django_toolbox.shopify_graphql_test import mock_response

from django_toolbox.apps.billing.tests import ShopifyViewTest
from ..collections import DraftOrderResponse
from ..draft_order import create_draft_order

from . import utils

APP_NAME = settings.APP_NAME

PRODUCTS_IN_COLLECTIONS = {
    "_159609389100": {
        "_4413823025196": True,
        "_4413823025195": True,
        "_4413823025197": False,
    },
    "_159609389101": {
        "_4413823025196": False,
        "_4413823025195": False,
        "_4413823025197": True,
    },
}

DRAFT_ORDER_CREATE_RESPONSE = DraftOrderResponse(
    id=123, invoice_url="http://example.com/"
)

VARIABLES_INPUT_CART_PRODUCT_QUANTITY_SAME_AS_OFFER_PRODUCT_QUANTITY = {
    "input": {
        "lineItems": [
            {
                "quantity": 2,
                "variantId": "gid://shopify/ProductVariant/31547677245484",
                "customAttributes": None,
                "appliedDiscount": None,
            },
            {
                "quantity": 1,
                "variantId": "gid://shopify/ProductVariant/31547677245485",
                "customAttributes": None,
                "appliedDiscount": None,
            },
        ],
        "tags": APP_NAME,
        "note": "",
        "appliedDiscount": None,
        "shippingAddress": None,
        "metafields": [],
    }
}

VARIABLES_INPUT_CART_PRODUCT_QUANTITY_OVER_OFFER_PRODUCT_QUANTITY = {
    "input": {
        "lineItems": [
            {
                "quantity": 2,
                "variantId": "gid://shopify/ProductVariant/31547677245484",
                "customAttributes": None,
                "appliedDiscount": None,
            },
            {
                "quantity": 1,
                "variantId": "gid://shopify/ProductVariant/31547677245485",
                "customAttributes": None,
                "appliedDiscount": None,
            },
            {
                "quantity": 1,
                "variantId": "gid://shopify/ProductVariant/31547677245485",
                "customAttributes": None,
                "appliedDiscount": None,
            },
        ],
        "tags": APP_NAME,
        "note": "",
        "appliedDiscount": None,
        "shippingAddress": None,
        "metafields": [],
    }
}

VARIABLES_INPUT_CART_PRODUCT_QUANTITY_UNDER_OFFER_PRODUCT_QUANTITY = {
    "input": {
        "lineItems": [
            {
                "quantity": 1,
                "variantId": "gid://shopify/ProductVariant/31547677245484",
                "customAttributes": None,
                "appliedDiscount": None,
            },
            {
                "quantity": 1,
                "variantId": "gid://shopify/ProductVariant/31547677245485",
                "customAttributes": None,
                "appliedDiscount": None,
            },
        ],
        "tags": APP_NAME,
        "note": "",
        "appliedDiscount": None,
        "shippingAddress": None,
        "metafields": [],
    }
}

DISCOUNT_DATA_CUSTOMER_BUYS_MIN_AMOUNT_VARIANT_GETS_VARIANT = {
    "codeDiscountNodeByCode": {
        "codeDiscount": {
            "__typename": "DiscountCodeBxgy",
            "appliesOncePerCustomer": False,
            "status": "ACTIVE",
            "title": "30PERCENTOFF",
            "usageLimit": None,
            "usesPerOrderLimit": None,
            "customerBuys": {
                "items": {
                    "productVariants": {
                        "edges": [
                            {
                                "node": {
                                    "id": "gid://shopify/ProductVariant/31547677245484"
                                }
                            }
                        ]
                    },
                    "products": {
                        "edges": [
                            {"node": {"id": "gid://shopify/Product/4413823025196"}}
                        ]
                    },
                },
                "value": {"amount": "500.0"},
            },
            "customerGets": {
                "items": {
                    "productVariants": {
                        "edges": [
                            {
                                "node": {
                                    "id": "gid://shopify/ProductVariant/31547677245485"
                                }
                            }
                        ]
                    },
                    "products": {
                        "edges": [
                            {"node": {"id": "gid://shopify/Product/4413823025197"}}
                        ]
                    },
                },
                "value": {"quantity": {"quantity": "1"}, "effect": {"percentage": 0.3}},
            },
        }
    }
}


DISCOUNT_DATA_CUSTOMER_BUYS_MIN_QUANTITY_COLLECTION_GETS_COLLECTION = {
    "codeDiscountNodeByCode": {
        "codeDiscount": {
            "__typename": "DiscountCodeBxgy",
            "appliesOncePerCustomer": False,
            "status": "ACTIVE",
            "title": "30PERCENTOFF",
            "usageLimit": None,
            "usesPerOrderLimit": None,
            "customerBuys": {
                "items": {
                    "collections": {
                        "edges": [
                            {"node": {"id": "gid://shopify/Collection/159609389100"}}
                        ]
                    }
                },
                "value": {"quantity": "2"},
            },
            "customerGets": {
                "items": {
                    "collections": {
                        "edges": [
                            {"node": {"id": "gid://shopify/Collection/159609389101"}}
                        ]
                    }
                },
                "value": {"quantity": {"quantity": "1"}, "effect": {"percentage": 0.3}},
            },
        }
    }
}


def get_offers_line_items(shop, data):
    return [], []


class CreateDraftOrderDiscountBuyXGetYViewTest(ShopifyViewTest):
    @responses.activate
    @patch(
        "django_toolbox.discounts.draft_order.execute_create_draft_order",
        return_value=DRAFT_ORDER_CREATE_RESPONSE,
    )
    def test_applies_discount_customer_buys_min_quantity_product_customer_gets_product(
        self, execute_mock
    ):
        mock_response(DISCOUNT_DATA_CUSTOMER_BUYS_MIN_AMOUNT_VARIANT_GETS_VARIANT)
        data = {
            "shop": self.shop.myshopify_domain,
            "cart": {
                "items": [
                    {
                        "quantity": 2,
                        "variant_id": 31547677245484,
                        "properties": None,
                        "line_price": 25000,
                        "product_id": 4413823025196,
                    },
                    {
                        "quantity": 2,
                        "variant_id": 31547677245485,
                        "properties": None,
                        "line_price": 25000,
                        "product_id": 4413823025197,
                    },
                ],
                "currency": "CZK",
                "total_price": 75000,
                "item_count": 3,
                "token": "cart_token",
                "attributes": {"greeting": "they"},
                "note": "",
            },
            "offers": [],
            "discount_code": "30PERCENTOFF",
        }

        create_draft_order(self.shop, data, get_offers_line_items)

        variables = execute_mock.call_args[0][1]
        expected_input = copy.deepcopy(
            VARIABLES_INPUT_CART_PRODUCT_QUANTITY_OVER_OFFER_PRODUCT_QUANTITY
        )
        expected_input["input"]["lineItems"][2]["appliedDiscount"] = {
            "title": "30PERCENTOFF",
            "value": 30,
            "valueType": "PERCENTAGE",
        }
        expected_input["input"]["customAttributes"] = [
            {"key": "greeting", "value": "they"}
        ]
        self.maxDiff = None
        self.assertDictEqual(variables, expected_input)

    @responses.activate
    @patch(
        "django_toolbox.discounts.draft_order.execute_create_draft_order",
        return_value=DRAFT_ORDER_CREATE_RESPONSE,
    )
    def test_applies_discount_customer_buys_min_amount_product_customer_gets_product(
        self, execute_mock
    ):
        discount_response = utils.discount_buys_defined_product_response_factory(
            buys_product_id=4413823025196,
            buys_min_quantity=2,
            gets_product_id=4413823025197,
            gets_quantity=1,
            discount_percentage=0.3,
        )
        mock_response(discount_response)
        data = {
            "shop": self.shop.myshopify_domain,
            "cart": {
                "items": [
                    {
                        "quantity": 2,
                        "variant_id": 31547677245484,
                        "properties": None,
                        "line_price": 25000,
                        "product_id": 4413823025196,
                    },
                    {
                        "quantity": 1,
                        "variant_id": 31547677245485,
                        "properties": None,
                        "line_price": 25000,
                        "product_id": 4413823025197,
                    },
                ],
                "currency": "CZK",
                "total_price": 75000,
                "item_count": 3,
                "token": "cart_token",
                "attributes": {"greeting": "they"},
                "note": "",
            },
            "offers": [],
            "discount_code": "30PERCENTOFF",
        }

        create_draft_order(self.shop, data, get_offers_line_items)

        variables = execute_mock.call_args[0][1]
        expected_input = copy.deepcopy(
            VARIABLES_INPUT_CART_PRODUCT_QUANTITY_SAME_AS_OFFER_PRODUCT_QUANTITY
        )
        expected_input["input"]["lineItems"][1]["appliedDiscount"] = {
            "title": "30PERCENTOFF",
            "value": 30,
            "valueType": "PERCENTAGE",
        }
        expected_input["input"]["customAttributes"] = [
            {"key": "greeting", "value": "they"}
        ]
        self.maxDiff = None
        self.assertDictEqual(variables, expected_input)

    @responses.activate
    @patch(
        "django_toolbox.discounts.draft_order.execute_create_draft_order",
        return_value=DRAFT_ORDER_CREATE_RESPONSE,
    )
    def test_not_applies_discount_customer_buys_min_quantity_product_customer_gets_product(
        self, execute_mock
    ):
        discount_response = utils.discount_buys_defined_product_response_factory(
            buys_product_id=4413823025196,
            buys_min_quantity=2,
            gets_product_id=4413823025197,
            gets_quantity=1,
            discount_percentage=0.3,
        )
        mock_response(discount_response)
        data = {
            "shop": self.shop.myshopify_domain,
            "cart": {
                "items": [
                    {
                        "quantity": 1,
                        "variant_id": 31547677245484,
                        "properties": None,
                        "line_price": 25000,
                        "product_id": 4413823025196,
                    },
                    {
                        "quantity": 1,
                        "variant_id": 31547677245485,
                        "properties": None,
                        "line_price": 25000,
                        "product_id": 4413823025197,
                    },
                ],
                "currency": "CZK",
                "total_price": 50000,
                "item_count": 2,
                "token": "cart_token",
                "attributes": {"greeting": "they"},
                "note": "",
            },
            "offers": [],
            "discount_code": "30PERCENTOFF",
        }

        create_draft_order(self.shop, data, get_offers_line_items)

        variables = execute_mock.call_args[0][1]
        expected_input = copy.deepcopy(
            VARIABLES_INPUT_CART_PRODUCT_QUANTITY_UNDER_OFFER_PRODUCT_QUANTITY
        )
        expected_input["input"]["customAttributes"] = [
            {"key": "greeting", "value": "they"}
        ]
        self.maxDiff = None
        self.assertDictEqual(variables, expected_input)

    @responses.activate
    @patch(
        "django_toolbox.discounts.draft_order.execute_create_draft_order",
        return_value=DRAFT_ORDER_CREATE_RESPONSE,
    )
    def test_applies_discount_customer_buys_min_quantity_collection_customer_gets_collection(
        self, execute_mock
    ):
        mock_response(
            DISCOUNT_DATA_CUSTOMER_BUYS_MIN_QUANTITY_COLLECTION_GETS_COLLECTION
        )
        mock_response(PRODUCTS_IN_COLLECTIONS)
        data = {
            "shop": self.shop.myshopify_domain,
            "cart": {
                "items": [
                    {
                        "quantity": 2,
                        "variant_id": 31547677245484,
                        "properties": None,
                        "line_price": 25000,
                        "product_id": 4413823025196,
                    },
                    {
                        "quantity": 1,
                        "variant_id": 31547677245485,
                        "properties": None,
                        "line_price": 25000,
                        "product_id": 4413823025197,
                    },
                ],
                "currency": "CZK",
                "total_price": 75000,
                "item_count": 3,
                "token": "cart_token",
                "attributes": {"greeting": "they"},
                "note": "",
            },
            "offers": [],
            "discount_code": "30PERCENTOFF",
        }

        create_draft_order(self.shop, data, get_offers_line_items)

        variables = execute_mock.call_args[0][1]
        expected_input = copy.deepcopy(
            VARIABLES_INPUT_CART_PRODUCT_QUANTITY_SAME_AS_OFFER_PRODUCT_QUANTITY
        )
        expected_input["input"]["lineItems"][1]["appliedDiscount"] = {
            "title": "30PERCENTOFF",
            "value": 30,
            "valueType": "PERCENTAGE",
        }
        expected_input["input"]["customAttributes"] = [
            {"key": "greeting", "value": "they"}
        ]
        self.maxDiff = None
        self.assertDictEqual(variables, expected_input)

    @responses.activate
    @patch(
        "django_toolbox.discounts.draft_order.execute_create_draft_order",
        return_value=DRAFT_ORDER_CREATE_RESPONSE,
    )
    def test_applies_discount_two_line_items_with_same_product_id_but_different_variant_id(
        self, execute_mock
    ):
        product_id = 4540446212178
        discount_response = utils.discount_buys_defined_product_response_factory(
            buys_product_id=product_id,
            buys_min_quantity=1,
            gets_product_id=product_id,
            gets_quantity=1,
            discount_percentage=0.15,
        )
        mock_response(discount_response)

        cart_items = [
            {
                "quantity": 1,
                "variant_id": 1,
                "properties": None,
                "line_price": 25000,
                "product_id": product_id,
            },
            {
                "quantity": 1,
                "variant_id": 2,
                "properties": None,
                "line_price": 25000,
                "product_id": product_id,
            },
        ]

        cart_data = {
            "shop": self.shop.myshopify_domain,
            "cart": {
                "items": cart_items,
                "currency": "CZK",
                "total_price": 50000,
                "item_count": 2,
                "token": "cart_token",
                "attributes": {"greeting": "they"},
                "note": "",
            },
            "offers": [],
            "discount_code": "30PERCENTOFF",
        }
        create_draft_order(self.shop, cart_data, get_offers_line_items)
        variables = execute_mock.call_args[0][1]

        line_items = variables["input"]["lineItems"]
        self.assertEqual(line_items[0]["appliedDiscount"]["value"], 15.0)
        self.assertIsNone(line_items[1]["appliedDiscount"])
