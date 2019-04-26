import logging

try:
    from elasticapm.instrumentation import register

    register.register("django_toolbox.shopify_instrumentation.ShopifyInstrumentation")
except:
    logging.info("elasticapm not found")
