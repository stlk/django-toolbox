def discount_buys_defined_product_response_factory(
    buys_product_id,
    buys_min_quantity,
    gets_product_id,
    gets_quantity,
    discount_percentage,
):
    assert discount_percentage <= 1.0
    return {
        "codeDiscountNodeByCode": {
            "codeDiscount": {
                "__typename": "DiscountCodeBxgy",
                "status": "ACTIVE",
                "usageLimit": None,
                "asyncUsageCount": 61,
                "customerBuys": {
                    "items": {
                        "productVariants": {"edges": []},
                        "products": {
                            "edges": [
                                {
                                    "node": {
                                        "id": f"gid:\/\/shopify\/Product\/{buys_product_id}"
                                    }
                                }
                            ]
                        },
                    },
                    "value": {"quantity": f"{buys_min_quantity}"},
                },
                "customerGets": {
                    "items": {
                        "productVariants": {"edges": []},
                        "products": {
                            "edges": [
                                {
                                    "node": {
                                        "id": f"gid:\/\/shopify\/Product\/{gets_product_id}"
                                    }
                                }
                            ]
                        },
                    },
                    "value": {
                        "quantity": {"quantity": f"{gets_quantity}"},
                        "effect": {"percentage": discount_percentage},
                    },
                },
            }
        }
    }
