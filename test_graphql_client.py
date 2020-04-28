import unittest

import responses

from django.conf import settings
from django_toolbox.shopify_graphql import GraphQLResponseError, run_query
from django_toolbox.shopify_graphql_test import mock_response

myshopify_domain = "example.com"


class GraphQLClientTest(unittest.TestCase):
    def set_success(self):
        mock_response({})

    @responses.activate
    def test_success(self):
        self.set_success()
        response = run_query("", myshopify_domain, "")
        self.assertDictEqual(response["data"], {})

    @responses.activate
    def test_raises_exception(self):

        responses.add(
            responses.POST,
            f"https://{myshopify_domain}/admin/api/{settings.SHOPIFY_APP_API_VERSION}/graphql.json",
            json={
                "errors": [
                    {
                        "message": "Operation name is required when multiple operations are present",
                        "locations": [{"line": 22, "column": 1}],
                        "fields": [],
                    }
                ]
            },
            status=200,
        )

        with self.assertRaises(GraphQLResponseError):
            response = run_query("", myshopify_domain, "")

    @responses.activate
    def test_retries_when_throttled(self):

        responses.add(
            responses.POST,
            f"https://{myshopify_domain}/admin/api/{settings.SHOPIFY_APP_API_VERSION}/graphql.json",
            json={
                "errors": [{"message": "Throttled"}],
                "extensions": {
                    "cost": {
                        "requestedQueryCost": 755,
                        "actualQueryCost": None,
                        "throttleStatus": {
                            "maximumAvailable": 1000,
                            "currentlyAvailable": 115,
                            "restoreRate": 50,
                        },
                    }
                },
            },
            status=200,
        )

        self.set_success()

        response = run_query("", myshopify_domain, "")


if __name__ == "__main__":
    unittest.main()
