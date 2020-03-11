import logging
from ua_parser import user_agent_parser


def should_set_none(request):
    user_agent = request.META.get("HTTP_USER_AGENT")
    if not user_agent:
        return True

    try:
        parsed_string = user_agent_parser.Parse(user_agent)
        browser = parsed_string["user_agent"]
        os = parsed_string["os"]

        if "Chrom" in browser["family"] and int(browser["major"]) < 67:
            return False
        if "Mac OS X" in os["family"] and os["major"] == "10" and os["minor"] == "14":
            return False
        if "iOS" in os["family"] and os["major"] == "12":
            return False
    except:
        logging.exception("User Agent resolution failed")

    return True


class SamesiteCookieMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if should_set_none(request):
            for cookie in response.cookies.keys():
                if cookie in ["sessionid", "csrftoken"]:
                    response.cookies[cookie]["samesite"] = "None"

        return response
