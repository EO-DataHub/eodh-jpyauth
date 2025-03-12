import logging

from oauthenticator.oauth2 import OAuthenticator, OAuthLoginHandler, OAuthLogoutHandler
from traitlets import Bool, Unicode

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)


class EODHLoginHandler(OAuthLoginHandler):
    def get(self):
        self.log.info("EODH Login")
        super().get()


class EODHLogoutHandler(OAuthLogoutHandler):
    """Log a user out by clearing both their JupyterHub login cookie and SSO cookie."""

    async def get(self):
        self.log.info("EODH Logout")
        if self.authenticator.enable_logout:
            await self.default_handle_logout()
            await self.handle_logout()

            redirect_url = self.authenticator.oauth_logout_url
            if self.authenticator.oauth_logout_redirect_uri:
                redirect_url += (
                    "?redirect_uri=%s" % self.authenticator.oauth_logout_redirect_uri
                )

            self.redirect(redirect_url)
        else:
            await super().get()


class EODHAuthenticator(OAuthenticator):
    login_service = "UK EO DataHub"
    client_id = Unicode(config=True)
    client_secret = Unicode(config=True)
    token_url = Unicode(config=True)
    userdata_url = Unicode(config=True)
    username_claim = Unicode("preferred_username", config=True)
    enable_logout = Bool(False, config=True)
    oauth_logout_url = Unicode(config=True)
    oauth_logout_redirect_uri = Unicode(config=True)

    # async def refresh_user(self, user, auth_state):
    #     print("Refreshing user %s", user)
    #     print("Auth state %s", auth_state)
    #     print("self %s", self)
    #     return None

    login_handler = EODHLoginHandler
    logout_handler = EODHLogoutHandler
    # refresh_user_hook = refresh_user
