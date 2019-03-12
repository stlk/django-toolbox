import logging
from time import time

from django.conf import settings

timing_logger = logging.getLogger("django.request")

SETTINGS = {"EXCLUDED_PATHS": set(), "LONG_REQUEST_THRESHOLD": 1000}
SETTINGS.update(getattr(settings, "METRICS", {}))
SETTINGS["EXCLUDED_PATHS"] = {path.strip("/") for path in SETTINGS["EXCLUDED_PATHS"]}


class TimingMiddleware:
    def __init__(self, get_response=None):
        self.get_response = get_response

    def process_request(self, request):
        if request.path.strip("/") in SETTINGS["EXCLUDED_PATHS"]:
            return request
        setattr(request, "_metrics_start_time", time())

    def process_response(self, request, response):

        if hasattr(request, "_metrics_start_time"):
            duration = time() - request._metrics_start_time
            duration_ms = int(round(duration * 1000))
            if duration_ms > SETTINGS["LONG_REQUEST_THRESHOLD"]:
                timing_logger.warning(f"Long request. duration_ms: {duration_ms}")
            else:
                timing_logger.info(f"duration_ms: {duration_ms}")

        return response

    def __call__(self, request):
        self.process_request(request)
        response = self.get_response(request)
        self.process_response(request, response)
        return response
