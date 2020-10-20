import copy
from unittest.mock import patch

from django.conf import settings
import responses

from django_toolbox.apps.billing.tests import ShopifyViewTest

from ...shopify_graphql_test import mock_response
from ..collections import DraftOrderResponse
from ..draft_order import create_draft_order


APP_NAME = settings.APP_NAME
PRODUCTS_IN_COLLECTIONS = {
    "_159609389100": {
        "_4413823025196": True,
        "_4413823025195": True,
        "_4413823025197": False,
    }
}

AMOUNT_DISCOUNT_DATA = {
    "codeDiscountNodeByCode": {
        "codeDiscount": {
            "status": "ACTIVE",
            "__typename": "DiscountCodeBasic",
            "minimumRequirement": {"greaterThanOrEqualToSubtotal": {"amount": "30.0"}},
            "customerGets": {
                "items": {"allItems": True},
                "value": {"amount": {"amount": "20.0"}, "appliesOnEachItem": False},
            },
        }
    }
}

AMOUNT_DISCOUNT_DATA_MIN_REQUIREMENTS_AMOUNT_FAIL = {
    "codeDiscountNodeByCode": {
        "codeDiscount": {
            "status": "ACTIVE",
            "__typename": "DiscountCodeBasic",
            "minimumRequirement": {
                "greaterThanOrEqualToSubtotal": {"amount": "3000000.0"}
            },
            "customerGets": {
                "items": {"allItems": True},
                "value": {"amount": {"amount": "20.0"}, "appliesOnEachItem": False},
            },
        }
    }
}

COLLECTIONS_FIXED_AMOUNT_DISCOUNT_DATA = {
    "codeDiscountNodeByCode": {
        "codeDiscount": {
            "status": "ACTIVE",
            "__typename": "DiscountCodeBasic",
            "minimumRequirement": None,
            "customerGets": {
                "items": {
                    "collections": {
                        "edges": [
                            {"node": {"id": "gid://shopify/Collection/159609389100"}}
                        ]
                    }
                },
                "value": {"amount": {"amount": "10.0"}, "appliesOnEachItem": False},
            },
        }
    }
}

CUSTOMER_GETS_ITEMS_AMOUNT_DISCOUNT_DATA = {
    "codeDiscountNodeByCode": {
        "codeDiscount": {
            "status": "ACTIVE",
            "__typename": "DiscountCodeBasic",
            "minimumRequirement": {"greaterThanOrEqualToQuantity": "2"},
            "customerGets": {
                "items": {
                    "products": {
                        "edges": [
                            {"node": {"id": "gid://shopify/Product/4413823025196"}},
                            {"node": {"id": "gid://shopify/Product/4413823156268"}},
                        ]
                    }
                },
                "value": {"amount": {"amount": "70.0"}, "appliesOnEachItem": False},
            },
        }
    }
}

CUSTOMER_GETS_ITEMS_AMOUNT_DISCOUNT_DATA_MIN_REQUIREMENTS_QUANTITY_FAIL = {
    "codeDiscountNodeByCode": {
        "codeDiscount": {
            "status": "ACTIVE",
            "__typename": "DiscountCodeBasic",
            "minimumRequirement": {"greaterThanOrEqualToQuantity": "10"},
            "customerGets": {
                "items": {
                    "products": {
                        "edges": [
                            {"node": {"id": "gid://shopify/Product/4413823025196"}},
                            {"node": {"id": "gid://shopify/Product/4413823156268"}},
                        ]
                    }
                },
                "value": {"amount": {"amount": "70.0"}, "appliesOnEachItem": False},
            },
        }
    }
}

CUSTOMER_GETS_ITEMS_AMOUNT_DISCOUNT_DATA_APPLIES_ON_EACH_ITEM = {
    "codeDiscountNodeByCode": {
        "codeDiscount": {
            "status": "ACTIVE",
            "__typename": "DiscountCodeBasic",
            "minimumRequirement": None,
            "customerGets": {
                "items": {
                    "products": {
                        "edges": [
                            {"node": {"id": "gid://shopify/Product/4413823025196"}},
                            {"node": {"id": "gid://shopify/Product/4413823156268"}},
                        ]
                    }
                },
                "value": {"amount": {"amount": "70.0"}, "appliesOnEachItem": True},
            },
        }
    }
}

PERCENTAGE_DISCOUNT_DATA = {
    "codeDiscountNodeByCode": {
        "codeDiscount": {
            "status": "ACTIVE",
            "__typename": "DiscountCodeBasic",
            "minimumRequirement": {"greaterThanOrEqualToQuantity": "2"},
            "customerGets": {
                "items": {"allItems": True},
                "value": {"percentage": 0.2, "appliesOnEachItem": False},
            },
        }
    }
}

CUSTOMER_GETS_ITEMS_PERCENTAGE_DISCOUNT_DATA = {
    "codeDiscountNodeByCode": {
        "codeDiscount": {
            "status": "ACTIVE",
            "__typename": "DiscountCodeBasic",
            "minimumRequirement": None,
            "customerGets": {
                "items": {
                    "products": {
                        "edges": [
                            {"node": {"id": "gid://shopify/Product/4413823025196"}},
                            {"node": {"id": "gid://shopify/Product/4413823156268"}},
                        ]
                    }
                },
                "value": {"percentage": 0.3, "appliesOnEachItem": False},
            },
        }
    }
}

CUSTOMER_GETS_VARIANTS_PERCENTAGE_DISCOUNT_DATA = {
    "codeDiscountNodeByCode": {
        "codeDiscount": {
            "status": "ACTIVE",
            "__typename": "DiscountCodeBasic",
            "minimumRequirement": None,
            "customerGets": {
                "items": {
                    "productVariants": {
                        "edges": [
                            {
                                "node": {
                                    "id": "gid://shopify/ProductVariant/31547677245484"
                                }
                            },
                            {
                                "node": {
                                    "id": "gid://shopify/ProductVariant/31547677278252"
                                }
                            },
                        ]
                    }
                },
                "value": {"percentage": 0.5, "appliesOnEachItem": False},
            },
        }
    }
}

COLLECTIONS_PERCENTAGE_DISCOUNT_DATA = {
    "codeDiscountNodeByCode": {
        "codeDiscount": {
            "status": "ACTIVE",
            "__typename": "DiscountCodeBasic",
            "minimumRequirement": None,
            "customerGets": {
                "items": {
                    "collections": {
                        "edges": [
                            {"node": {"id": "gid://shopify/Collection/159609389100"}}
                        ]
                    }
                },
                "value": {"percentage": 0.7, "appliesOnEachItem": False},
            },
        }
    }
}

VARIABLES_INPUT = {
    "input": {
        "lineItems": [
            {
                "quantity": 2,
                "variantId": "gid://shopify/ProductVariant/17744973103175",
                "customAttributes": None,
                "appliedDiscount": None,
            }
        ],
        "tags": APP_NAME,
        "note": "",
        "appliedDiscount": None,
        "shippingAddress": None,
        "metafields": [],
    }
}


MULTIPLE_VARIABLES_INPUT = {
    "input": {
        "lineItems": [
            {
                "quantity": 2,
                "variantId": "gid://shopify/ProductVariant/17744973103175",
                "customAttributes": None,
                "appliedDiscount": None,
            },
            {
                "quantity": 1,
                "variantId": "gid://shopify/ProductVariant/17744973103171",
                "customAttributes": None,
                "appliedDiscount": None,
            },
            {
                "quantity": 1,
                "variantId": "gid://shopify/ProductVariant/17744973103172",
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

DRAFT_ORDER_CREATE_RESPONSE = DraftOrderResponse(
    id=123, invoice_url="http://example.com/"
)


def get_offers_line_items(shop, data):
    return [], []


class CreateDraftOrderDiscountBasicViewTest(ShopifyViewTest):
    @responses.activate
    @patch(
        "django_toolbox.discounts.draft_order.execute_create_draft_order",
        return_value=DRAFT_ORDER_CREATE_RESPONSE,
    )
    def test_applies_discount_fixed_amount_all_items(self, execute_mock):
        mock_response(AMOUNT_DISCOUNT_DATA)
        data = {
            "shop": self.shop.myshopify_domain,
            "cart": {
                "items": [
                    {
                        "quantity": 2,
                        "variant_id": 17_744_973_103_175,
                        "properties": None,
                        "price": 25000,
                        "product_id": 4413820174380,
                    }
                ],
                "currency": "CZK",
                "total_price": 50000,
                "item_count": 2,
                "token": "cart_token",
                "attributes": {"greeting": "they"},
                "note": "",
            },
            "offers": [],
            "discount_code": "20FIXEDOFF",
        }

        create_draft_order(self.shop, data, get_offers_line_items)

        variables = execute_mock.call_args[0][1]

        expected_input = copy.deepcopy(VARIABLES_INPUT)
        expected_input["input"]["appliedDiscount"] = {
            "title": "20FIXEDOFF",
            "value": 20.0,
            "valueType": "FIXED_AMOUNT",
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
    def test_applies_discount_fixed_amount_all_items_fail_min_requirements_amount(
        self, execute_mock
    ):
        mock_response(AMOUNT_DISCOUNT_DATA_MIN_REQUIREMENTS_AMOUNT_FAIL)
        data = {
            "shop": self.shop.myshopify_domain,
            "cart": {
                "items": [
                    {
                        "quantity": 2,
                        "variant_id": 17_744_973_103_175,
                        "properties": None,
                        "price": 25000,
                        "product_id": 4413820174380,
                    }
                ],
                "currency": "CZK",
                "total_price": 5000,
                "item_count": 2,
                "token": "cart_token",
                "attributes": {"greeting": "they"},
                "note": "",
            },
            "offers": [],
            "discount_code": "20FIXEDOFF",
        }

        create_draft_order(self.shop, data, get_offers_line_items)

        variables = execute_mock.call_args[0][1]
        expected_input = copy.deepcopy(VARIABLES_INPUT)
        expected_input["input"]["appliedDiscount"] = {
            "title": "20FIXEDOFF",
            "value": 20.0,
            "valueType": "FIXED_AMOUNT",
        }
        expected_input["input"]["customAttributes"] = [
            {"key": "greeting", "value": "they"}
        ]
        self.maxDiff = None
        self.assertNotEqual(variables, expected_input)

    @responses.activate
    @patch(
        "django_toolbox.discounts.draft_order.execute_create_draft_order",
        return_value=DRAFT_ORDER_CREATE_RESPONSE,
    )
    def test_applies_discount_fixed_amount_collections(self, execute_mock):
        mock_response(COLLECTIONS_FIXED_AMOUNT_DISCOUNT_DATA)
        mock_response(PRODUCTS_IN_COLLECTIONS)
        data = {
            "shop": self.shop.myshopify_domain,
            "cart": {
                "items": [
                    {
                        "quantity": 2,
                        "variant_id": 31547677245484,
                        "properties": None,
                        "price": 25000,
                        "product_id": 4413823025196,
                    },
                    {
                        "quantity": 1,
                        "variant_id": 31547677245485,
                        "properties": None,
                        "price": 10000,
                        "product_id": 4413823025195,
                    },
                    {
                        "quantity": 1,
                        "variant_id": 31547677245487,
                        "properties": None,
                        "price": 10000,
                        "product_id": 4413823025197,
                    },
                ],
                "currency": "CZK",
                "total_price": 50000,
                "token": "cart_token",
                "attributes": {"greeting": "they"},
                "note": "",
            },
            "offers": [],
            "discount_code": "10FIXEDOFF",
        }

        create_draft_order(self.shop, data, get_offers_line_items)

        variables = execute_mock.call_args[0][1]
        expected_input = copy.deepcopy(MULTIPLE_VARIABLES_INPUT)
        expected_input["input"]["lineItems"][0]["appliedDiscount"] = {
            "title": "10FIXEDOFF",
            "value": 3.33,
            "valueType": "FIXED_AMOUNT",
        }
        expected_input["input"]["lineItems"][1]["appliedDiscount"] = {
            "title": "10FIXEDOFF",
            "value": 3.33,
            "valueType": "FIXED_AMOUNT",
        }
        expected_input["input"]["lineItems"][0][
            "variantId"
        ] = "gid://shopify/ProductVariant/31547677245484"
        expected_input["input"]["lineItems"][1][
            "variantId"
        ] = "gid://shopify/ProductVariant/31547677245485"
        expected_input["input"]["lineItems"][2][
            "variantId"
        ] = "gid://shopify/ProductVariant/31547677245487"
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
    def test_applies_discount_percentage_all_items(self, execute_mock):
        mock_response(PERCENTAGE_DISCOUNT_DATA)
        data = {
            "shop": self.shop.myshopify_domain,
            "cart": {
                "items": [
                    {
                        "quantity": 2,
                        "variant_id": 17_744_973_103_175,
                        "properties": None,
                        "price": 25000,
                        "product_id": 4413820174380,
                    }
                ],
                "currency": "CZK",
                "total_price": 50000,
                "item_count": 2,
                "token": "cart_token",
                "attributes": {"greeting": "they"},
                "note": "",
            },
            "offers": [],
            "discount_code": "20PERCENTOFF",
        }

        create_draft_order(self.shop, data, get_offers_line_items)

        variables = execute_mock.call_args[0][1]
        expected_input = copy.deepcopy(VARIABLES_INPUT)
        expected_input["input"]["appliedDiscount"] = {
            "title": "20PERCENTOFF",
            "value": 20,
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
    def test_applies_discount_fixed_amount_customer_gets_items(self, execute_mock):
        mock_response(CUSTOMER_GETS_ITEMS_AMOUNT_DISCOUNT_DATA)
        data = {
            "shop": self.shop.myshopify_domain,
            "cart": {
                "items": [
                    {
                        "quantity": 2,
                        "variant_id": 31547677245484,
                        "properties": None,
                        "price": 25000,
                        "product_id": 4413823025196,
                    }
                ],
                "currency": "CZK",
                "total_price": 50000,
                "item_count": 2,
                "token": "cart_token",
                "attributes": {"greeting": "they"},
                "note": "",
            },
            "offers": [],
            "discount_code": "70FIXEDOFF",
        }

        create_draft_order(self.shop, data, get_offers_line_items)

        variables = execute_mock.call_args[0][1]
        expected_input = copy.deepcopy(VARIABLES_INPUT)
        expected_input["input"]["customAttributes"] = [
            {"key": "greeting", "value": "they"}
        ]
        expected_input["input"]["lineItems"][0]["appliedDiscount"] = {
            "title": "70FIXEDOFF",
            "value": 35.0,
            "valueType": "FIXED_AMOUNT",
        }

        expected_input["input"]["lineItems"][0][
            "variantId"
        ] = "gid://shopify/ProductVariant/31547677245484"
        expected_input["input"]["appliedDiscount"] = None
        self.maxDiff = None
        self.assertDictEqual(variables, expected_input)

    @responses.activate
    @patch(
        "django_toolbox.discounts.draft_order.execute_create_draft_order",
        return_value=DRAFT_ORDER_CREATE_RESPONSE,
    )
    def test_applies_discount_fixed_amount_customer_gets_items_min_requirements_quantity_fail(
        self, execute_mock
    ):
        mock_response(
            CUSTOMER_GETS_ITEMS_AMOUNT_DISCOUNT_DATA_MIN_REQUIREMENTS_QUANTITY_FAIL
        )
        data = {
            "shop": self.shop.myshopify_domain,
            "cart": {
                "items": [
                    {
                        "quantity": 2,
                        "variant_id": 31547677245484,
                        "properties": None,
                        "price": 25000,
                        "product_id": 4413823025196,
                    }
                ],
                "currency": "CZK",
                "total_price": 50000,
                "item_count": 2,
                "token": "cart_token",
                "attributes": {"greeting": "they"},
                "note": "",
            },
            "offers": [],
            "discount_code": "70FIXEDOFF",
        }

        create_draft_order(self.shop, data, get_offers_line_items)

        variables = execute_mock.call_args[0][1]
        expected_input = copy.deepcopy(VARIABLES_INPUT)
        expected_input["input"]["customAttributes"] = [
            {"key": "greeting", "value": "they"}
        ]
        expected_input["input"]["lineItems"][0]["appliedDiscount"] = {
            "title": "70FIXEDOFF",
            "value": 70.0,
            "valueType": "FIXED_AMOUNT",
        }

        expected_input["input"]["lineItems"][0][
            "variantId"
        ] = "gid://shopify/ProductVariant/31547677245484"
        expected_input["input"]["appliedDiscount"] = None
        self.maxDiff = None
        self.assertNotEqual(variables, expected_input)

    @responses.activate
    @patch(
        "django_toolbox.discounts.draft_order.execute_create_draft_order",
        return_value=DRAFT_ORDER_CREATE_RESPONSE,
    )
    def test_applies_discount_fixed_amount_customer_gets_items_applies_on_each_item(
        self, execute_mock
    ):
        mock_response(CUSTOMER_GETS_ITEMS_AMOUNT_DISCOUNT_DATA_APPLIES_ON_EACH_ITEM)
        data = {
            "shop": self.shop.myshopify_domain,
            "cart": {
                "items": [
                    {
                        "quantity": 2,
                        "variant_id": 31547677245484,
                        "properties": None,
                        "price": 25000,
                        "product_id": 4413823025196,
                    }
                ],
                "currency": "CZK",
                "total_price": 50000,
                "item_count": 2,
                "token": "cart_token",
                "attributes": {"greeting": "they"},
                "note": "",
            },
            "offers": [],
            "discount_code": "70FIXEDOFF",
        }

        create_draft_order(self.shop, data, get_offers_line_items)

        variables = execute_mock.call_args[0][1]
        expected_input = copy.deepcopy(VARIABLES_INPUT)
        expected_input["input"]["customAttributes"] = [
            {"key": "greeting", "value": "they"}
        ]
        expected_input["input"]["lineItems"][0]["appliedDiscount"] = {
            "title": "70FIXEDOFF",
            "value": 70.0,
            "valueType": "FIXED_AMOUNT",
        }

        expected_input["input"]["lineItems"][0][
            "variantId"
        ] = "gid://shopify/ProductVariant/31547677245484"
        expected_input["input"]["appliedDiscount"] = None
        self.maxDiff = None
        self.assertDictEqual(variables, expected_input)

    @responses.activate
    @patch(
        "django_toolbox.discounts.draft_order.execute_create_draft_order",
        return_value=DRAFT_ORDER_CREATE_RESPONSE,
    )
    def test_applies_discount_percentage_customer_gets_items(self, execute_mock):
        mock_response(CUSTOMER_GETS_ITEMS_PERCENTAGE_DISCOUNT_DATA)
        data = {
            "shop": self.shop.myshopify_domain,
            "cart": {
                "items": [
                    {
                        "quantity": 2,
                        "variant_id": 31547677245484,
                        "properties": None,
                        "price": 25000,
                        "product_id": 4413823025196,
                    }
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
        expected_input = copy.deepcopy(VARIABLES_INPUT)
        expected_input["input"]["lineItems"][0]["appliedDiscount"] = {
            "title": "30PERCENTOFF",
            "value": 30,
            "valueType": "PERCENTAGE",
        }
        expected_input["input"]["lineItems"][0][
            "variantId"
        ] = "gid://shopify/ProductVariant/31547677245484"
        expected_input["input"]["appliedDiscount"] = None
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
    def test_applies_discount_percentage_customer_gets_variants(self, execute_mock):
        mock_response(CUSTOMER_GETS_VARIANTS_PERCENTAGE_DISCOUNT_DATA)
        data = {
            "shop": self.shop.myshopify_domain,
            "cart": {
                "items": [
                    {
                        "quantity": 2,
                        "variant_id": 31547677245484,
                        "properties": None,
                        "price": 25000,
                        "product_id": 4413823025196,
                    },
                    {
                        "quantity": 1,
                        "variant_id": 31547677278252,
                        "properties": None,
                        "price": 30000,
                        "product_id": 4413823156268,
                    },
                ],
                "currency": "CZK",
                "total_price": 80000,
                "item_count": 3,
                "token": "cart_token",
                "attributes": {"greeting": "they"},
                "note": "",
            },
            "offers": [],
            "discount_code": "50PERCENTOFF",
        }

        create_draft_order(self.shop, data, get_offers_line_items)

        variables = execute_mock.call_args[0][1]
        expected_input = copy.deepcopy(VARIABLES_INPUT)
        expected_input["input"]["lineItems"] = [
            {
                "quantity": 2,
                "variantId": "gid://shopify/ProductVariant/31547677245484",
                "customAttributes": None,
                "appliedDiscount": {
                    "title": "50PERCENTOFF",
                    "value": 50,
                    "valueType": "PERCENTAGE",
                },
            },
            {
                "quantity": 1,
                "variantId": "gid://shopify/ProductVariant/31547677278252",
                "customAttributes": None,
                "appliedDiscount": {
                    "title": "50PERCENTOFF",
                    "value": 50,
                    "valueType": "PERCENTAGE",
                },
            },
        ]
        expected_input["input"]["appliedDiscount"] = None
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
    def test_applies_discount_percentage_collections(self, execute_mock):
        mock_response(COLLECTIONS_PERCENTAGE_DISCOUNT_DATA)
        mock_response(PRODUCTS_IN_COLLECTIONS)
        data = {
            "shop": self.shop.myshopify_domain,
            "cart": {
                "items": [
                    {
                        "quantity": 2,
                        "variant_id": 31547677245484,
                        "properties": None,
                        "price": 25000,
                        "product_id": 4413823025196,
                    }
                ],
                "currency": "CZK",
                "total_price": 50000,
                "token": "cart_token",
                "attributes": {"greeting": "they"},
                "note": "",
            },
            "offers": [],
            "discount_code": "70PERCENTOFF",
        }

        create_draft_order(self.shop, data, get_offers_line_items)

        variables = execute_mock.call_args[0][1]
        expected_input = copy.deepcopy(VARIABLES_INPUT)
        expected_input["input"]["lineItems"][0]["appliedDiscount"] = {
            "title": "70PERCENTOFF",
            "value": 70,
            "valueType": "PERCENTAGE",
        }
        expected_input["input"]["lineItems"][0][
            "variantId"
        ] = "gid://shopify/ProductVariant/31547677245484"
        expected_input["input"]["customAttributes"] = [
            {"key": "greeting", "value": "they"}
        ]
        self.maxDiff = None
        self.assertDictEqual(variables, expected_input)
