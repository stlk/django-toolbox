import shopify
from django.conf import settings
from pyactiveresource.connection import UnauthorizedAccess


def has_scripts(shop):
    try:
        with shop.session:
            return any(shopify.ScriptTag.find())
    except UnauthorizedAccess as e:
        return None


def create_script(shop, scope="all"):
    with shop.session:
        script = shopify.ScriptTag().create(
            attributes={
                "event": "onload",
                "src": settings.SCRIPT_TAG_URL,
                "display_scope": scope,
            }
        )
        assert not script.errors, script.errors.full_messages()


def delete_script(shop):
    with shop.session:
        script_tags = shopify.ScriptTag.find()
        for script_tag in script_tags:
            script_tag.destroy()
