import os

# Django-toolbox auth settings
SOCIAL_AUTH_TRAILING_SLASH = False
SOCIAL_AUTH_URL_NAMESPACE = "auth:social"
SOCIAL_AUTH_USER_FIELDS = ["username"]
SOCIAL_AUTH_USERNAME_IS_FULL_EMAIL = True
SOCIAL_AUTH_USE_UNIQUE_USER_ID = False

SOCIAL_AUTH_LOGIN_REDIRECT_URL = "/admin"

SOCIAL_AUTH_NEW_USER_REDIRECT_URL = SOCIAL_AUTH_LOGIN_REDIRECT_URL
SOCIAL_AUTH_NEW_ASSOCIATION_REDIRECT_URL = SOCIAL_AUTH_LOGIN_REDIRECT_URL
SOCIAL_AUTH_INACTIVE_USER_URL = SOCIAL_AUTH_LOGIN_REDIRECT_URL

# Google Auth0
SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = os.environ.get("SOCIAL_AUTH_GOOGLE_OAUTH2_KEY")
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = os.environ.get("SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET")

SOCIAL_AUTH_PIPELINE = (
    "social_core.pipeline.social_auth.social_details",
    "social_core.pipeline.social_auth.social_uid",
    "social_core.pipeline.social_auth.social_user",
    # 'social_core.pipeline.user.get_username',
    # 'social_core.pipeline.social_auth.associate_by_email',
    "social_core.pipeline.user.create_user",
    "social_core.pipeline.social_auth.associate_user",
    "social_core.pipeline.social_auth.load_extra_data",
    "social_core.pipeline.user.user_details",
)
