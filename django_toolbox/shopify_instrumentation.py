from elasticapm.instrumentation.packages.base import AbstractInstrumentedModule
from elasticapm.traces import capture_span


class ShopifyInstrumentation(AbstractInstrumentedModule):
    name = "shopify-api"

    instrument_list = [("shopify.base", "ShopifyConnection._open")]

    def call(self, module, method, wrapped, instance, args, kwargs):

        with capture_span(
            f"{args[0]} {args[1]}",
            "ext.http.shopify",
            {"http": {"url": args[1]}},
            leaf=True,
        ):
            return wrapped(*args, **kwargs)
