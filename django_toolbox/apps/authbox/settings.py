import os

# Django-toolbox auth settings
SOCIAL_AUTH_TRAILING_SLASH = False
SOCIAL_AUTH_AUTH0_DOMAIN = os.environ.get("AUTH0_DOMAIN")
SOCIAL_AUTH_AUTH0_KEY = os.environ.get("AUTH0_KEY")
SOCIAL_AUTH_AUTH0_SECRET = os.environ.get("AUTH0_SECRET")
SOCIAL_AUTH_AUTH0_SCOPE = ["openid", "profile"]
SOCIAL_AUTH_URL_NAMESPACE = "auth:social"
SOCIAL_AUTH_USER_FIELDS = ["username"]

SOCIAL_AUTH_LOGIN_REDIRECT_URL = "/admin"
SOCIAL_AUTH_NEW_ASSOCIATION_REDIRECT_URL = SOCIAL_AUTH_LOGIN_REDIRECT_URL

SOCIAL_AUTH_NEW_USER_REDIRECT_URL = "/auth/new-user"
SOCIAL_AUTH_INACTIVE_USER_URL = SOCIAL_AUTH_NEW_USER_REDIRECT_URL
