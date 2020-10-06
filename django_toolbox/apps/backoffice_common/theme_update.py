import datetime
import logging
import re

from django.conf import settings
from django.contrib.auth import get_user_model
from pyactiveresource.connection import ResourceNotFound
import shopify


APP_NAME = settings.APP_NAME
CONFIG_ASSET_KEY = f"assets/{APP_NAME}-config.js"
snippet_key = f"snippets/digismoothie-{APP_NAME}.liquid"
close_head_regex = r"</head>"
close_head_replacement = f"""
{{% render 'digismoothie-{APP_NAME}' %}}
</head>
"""


def check_for_app(asset):
    if f"digismoothie-{APP_NAME}" in asset.value:
        logging.warning(
            f"{asset.key} already contains digismoothie-{APP_NAME}. Ignoring"
        )
        return True


def update_asset(asset):
    logging.info(f"Updating {asset.key} ...")
    close_head_match = re.search(close_head_regex, asset.value)

    assert close_head_match, f"</head> couldn't be found in: {asset.key}"
    asset.value = re.sub(close_head_match[0], close_head_replacement, asset.value)
    assert asset.save()


def backup_asset(asset, theme_id):
    logging.info(f"Backing up {asset.key} ...")

    directory, file_name = asset.key.split("/")
    backup_time = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    shopify.Asset().create(
        attributes={
            "key": f"{directory}/{APP_NAME}-backup-{backup_time}-{file_name}",
            "source_key": asset.key,
            "theme_id": theme_id,
        }
    )


def find_config_asset(main_theme_id):
    try:
        return shopify.Asset.find(theme_id=main_theme_id, key=CONFIG_ASSET_KEY)
    except ResourceNotFound as e:
        logging.info(f"Creating {CONFIG_ASSET_KEY} ...")

        return shopify.Asset().create(
            attributes={"key": CONFIG_ASSET_KEY, "theme_id": main_theme_id,}
        )


def update_config_asset(main_theme_id, value):
    config_asset = shopify.Asset.find(theme_id=main_theme_id, key=CONFIG_ASSET_KEY)
    config_asset.value = value
    config_asset.save()
    return value


def update_snippet(main_theme_id, enable_document_listener):
    javascript = ""
    if enable_document_listener:
        javascript = f"{APP_NAME.upper()}_DOCUMENT_LISTENER = true;"

    value = f"""
    <!-- {APP_NAME}-script -->
    <script>
        {javascript}
    </script>
    {{{{ '{APP_NAME}-config.js' | asset_url | script_tag }}}}
    <script src="{settings.SCRIPT_TAG_URL}?shop={{{{shop.permanent_domain}}}}"></script>
    <!-- / {APP_NAME}-script -->
    """
    find_config_asset(main_theme_id)
    return set_snippet(main_theme_id, value)


def set_snippet(main_theme_id, value):
    try:
        asset = shopify.Asset.find(theme_id=main_theme_id, key=snippet_key)
    except ResourceNotFound as e:
        asset = shopify.Asset()
        asset.theme_id = main_theme_id
        asset.key = snippet_key

    asset.value = value
    asset.save()
    return value


def get_main_theme_id():
    main_themes = shopify.Theme.find(role="main")
    assert main_themes, "Couldn't find a main theme"
    return main_themes[0].id


def get_snippet():
    main_theme_id = get_main_theme_id()
    try:
        asset = shopify.Asset.find(theme_id=main_theme_id, key=snippet_key)
        return asset.value
    except ResourceNotFound:
        return


def get_theme_liquid_content(main_theme_id):
    theme_asset = shopify.Asset.find(theme_id=main_theme_id, key="layout/theme.liquid")

    return theme_asset.value


def check_and_modify_theme_file(main_theme_id):
    theme_asset = shopify.Asset.find(theme_id=main_theme_id, key="layout/theme.liquid")
    logging.info(f"Found {theme_asset.key}")

    if not check_for_app(theme_asset):
        backup_asset(theme_asset, main_theme_id)
        update_asset(theme_asset)
        return True


def update_theme():
    main_theme_id = get_main_theme_id()
    theme_modified = check_and_modify_theme_file(main_theme_id)
    if theme_modified:
        update_snippet(main_theme_id, True)


def update_theme_task(myshopify_domain: str):
    user = get_user_model()
    shop = user.objects.get(myshopify_domain=myshopify_domain)
    with shop.session:
        update_theme()
