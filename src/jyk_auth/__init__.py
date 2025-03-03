import logging

from oauthenticator.oauth2 import OAuthenticator
from traitlets import Unicode

logger = logging.getLogger(__name__)


class EODHAuthenticator(OAuthenticator):
    login_service = "Keycloak"
    client_id = Unicode(config=True)
    client_secret = Unicode(config=True)
    token_url = Unicode(config=True)
    userdata_url = Unicode(config=True)
    username_claim = Unicode("preferred_username", config=True)
