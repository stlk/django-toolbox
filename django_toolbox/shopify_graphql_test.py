import responses
from django.conf import settings


def mock_response(myshopify_domain, data):
    responses.add(
        responses.POST,
        f"https://{myshopify_domain}/admin/api/{settings.SHOPIFY_APP_API_VERSION}/graphql.json",
        json={
            "data": data,
            "extensions": {
                "cost": {
                    "requestedQueryCost": 253,
                    "actualQueryCost": 6,
                    "throttleStatus": {
                        "maximumAvailable": 1000,
                        "currentlyAvailable": 994,
                        "restoreRate": 50,
                    },
                }
            },
        },
        status=200,
    )
