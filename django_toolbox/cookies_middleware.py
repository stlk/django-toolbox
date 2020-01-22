class SamesiteCookieMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        for cookie in response.cookies.keys():
            response.cookies[cookie]["samesite"] = "None"

        return response
