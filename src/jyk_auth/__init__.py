import json
import logging
import urllib.parse

from oauthenticator.oauth2 import OAuthenticator
from tornado import gen
from traitlets import Unicode

logger = logging.getLogger(__name__)


class JyKAuthenticator(OAuthenticator):
    login_service = "Keycloak"
    client_id = Unicode(config=True)
    client_secret = Unicode(config=True)
    token_url = Unicode(config=True)
    userdata_url = Unicode(config=True)
    username_key = Unicode("preferred_username", config=True)

    @gen.coroutine
    def authenticate(self, handler, data=None):
        code = handler.get_argument("code")
        params = {
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": self.get_callback_url(handler),
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
        }
        token_resp = yield self.http_client.fetch(
            self.token_url,
            method="POST",
            headers=headers,
            body=urllib.parse.urlencode(params),
        )
        token_data = json.loads(token_resp.body.decode("utf8", "replace"))
        access_token = token_data["access_token"]

        user_resp = yield self.http_client.fetch(
            self.userdata_url,
            method="GET",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        user_data = json.loads(user_resp.body.decode("utf8", "replace"))
        username = user_data[self.username_key]

        return {
            "name": username,
            "auth_state": {
                "access_token": access_token,
                "user_data": user_data,
            },
        }
