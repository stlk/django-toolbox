# Django-toolbox auth settings
SOCIAL_AUTH_TRAILING_SLASH = False  # Remove trailing slash from routes
SOCIAL_AUTH_AUTH0_DOMAIN = 'digismoothie.eu.auth0.com'
SOCIAL_AUTH_AUTH0_KEY = 'GfvodexWANzUMDbeOepVM6ShVJsky9KI'
SOCIAL_AUTH_AUTH0_SECRET = '3XhLWnDGCK1lLgThDT8A1gXtNNILT6brulBsyE20bq8QS6QN9GqpqZTbeDJe99Av'
SOCIAL_AUTH_AUTH0_SCOPE = [
    'openid',
    'profile',
]
SOCIAL_AUTH_URL_NAMESPACE = "auth:social"
SOCIAL_AUTH_USER_FIELDS = []
SOCIAL_AUTH_LOGIN_REDIRECT_URL = "/admin"