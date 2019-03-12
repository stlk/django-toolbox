import logging
from request_logging.middleware import LoggingMiddleware as LoggingMiddlewareBase


class LoggingMiddleware(LoggingMiddlewareBase):
    def _log_request(self, request):
        method_path = "{} {}".format(request.method, request.get_full_path())

        logging_context = self._get_logging_context(request, None)
        self.logger.log(logging.INFO, method_path, logging_context)
        # self._log_request_headers(request, logging_context)
        self._log_request_body(request, logging_context)

    def _log_resp(self, level, response, logging_context):
        pass

    def _skip_logging_request(self, request, reason):
        pass
