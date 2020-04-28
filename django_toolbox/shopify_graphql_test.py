import re
import responses


def mock_response(data):
    responses.add(
        responses.POST,
        re.compile(r".*\/graphql\.json"),
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
