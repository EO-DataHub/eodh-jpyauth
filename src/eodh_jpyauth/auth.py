import json
from typing import TypedDict

import jwt
import requests
import tornado.httpclient
from oauthenticator.oauth2 import OAuthenticator, OAuthLogoutHandler
from traitlets import Bool, Unicode


class TokenInfo(TypedDict):
    access_token: str
    expires_in: int
    refresh_token: str
    refresh_expires_in: int
    scope: str


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
                    f"?redirect_uri={self.authenticator.oauth_logout_redirect_uri}"
                )

            self.redirect(redirect_url)
        else:
            await super().get()


class EODHAuthenticator(OAuthenticator):
    enable_logout = Bool(False, config=True)
    oauth_logout_url = Unicode(config=True)
    oauth_logout_redirect_uri = Unicode(config=True)

    logout_handler = EODHLogoutHandler

    # async def token_to_user(self, token_info):
    #     """
    #     Determines who the logged-in user by decoding the access token.

    #     Args:
    #         token_info: the dictionary returned by the token request (exchanging the OAuth code for an Access Token)

    #     Returns:
    #         the JSON response to the `userdata_url` request.

    #     Called by :meth:`.authenticate` and :meth:`.refresh_user`.
    #     """
    #     try:
    #         return jwt.decode(
    #             token_info["access_token"],
    #             audience=self.client_id,
    #             options=dict(verify_signature=False),
    #         )
    #     except jwt.exceptions.ExpiredSignatureError:
    #         raise tornado.httpclient.HTTPClientError(
    #             403, "Session has expired. Please log in again."
    #         )
    #     except jwt.exceptions.ExpiredSignatureError:
    #         raise tornado.httpclient.HTTPClientError(
    #             403, "Invalid token audience. Please check OIDC configuration."
    #         )
    #     except Exception as err:
    #         raise tornado.httpclient.HTTPClientError(
    #             500,
    #             f"Unable to decode access token: {token_info['access_token']}\nError: {err}",
    #         )

    async def refresh_user(self, user, handler=None, **kwargs):
        """
        Refresh user authentication

        If auth_state is enabled, constructs a fresh user model
        (the same as `authenticate`)
        using the access_token in auth_state.
        If requests with the access token fail
        (e.g. because the token has expired)
        and a refresh token is found, attempts to exchange
        the refresh token for a new access token to store in auth_state.
        If the access token still fails after refresh,
        return False to require the user to login via oauth again.

        Set `Authenticator.auth_refresh_age = 0` to disable.

        Returns
        -------

        True:
          If auth info is up-to-date and needs no changes
          (always if `enable_auth_state` is False)
        False:
          If the user needs to login again
          (e.g. tokens in `auth_state` unavailable or expired)
        auth_model: dict
          The same dict as `authenticate`, updating any fields that should change.
          Can include things like group membership,
          but in OAuthenticator this mainly refreshes
          the token fields in `auth_state`.
        """
        self.log.info("Refreshing user with handler '%r'", handler)
        if not self.enable_auth_state:
            # auth state not enabled, can't refresh
            return True

        auth_state = await user.get_auth_state()
        self.log.info("pre-refresh: %s", json.dumps(auth_state, indent=2))

        if self.refresh_user_hook is not None:
            self.log.info("Calling refresh_user_hook...")
            refreshed = await self._call_refresh_user_hook(user, auth_state)
            if refreshed is not None:
                return refreshed

        if not auth_state:
            self.log.info(
                f"No auth_state found for user {user.name} refresh, need full authentication",
            )
            return False

        token_info = auth_state.get("token_response")
        auth_model = None
        try:
            auth_model = await self._token_to_auth_model(token_info)
        except tornado.httpclient.HTTPClientError as e:
            # assume any client error means an expired token
            # most likely 401 or 403 for well-behaved providers
            if 400 <= e.code < 500:
                self.log.info(
                    f"Error refreshing auth with current access_token for {user.name}: {e}. Will try to refresh, if possible."
                )
            else:
                raise
        refresh_token = auth_state.get("refresh_token", None)
        self.log.debug("refresh_token: %s", refresh_token)
        if refresh_token and not auth_model:
            self.log.info(f"Refreshing oauth access token for {user.name}")
            # access_token expired, try refreshing with refresh_token
            refresh_token_params = self.build_refresh_token_request_params(
                refresh_token
            )
            try:
                token_info = await self.get_token_info(handler, refresh_token_params)
                self.log.debug(
                    "refreshed token info: %s", json.dumps(token_info, indent=2)
                )
            except Exception as e:
                self.log.info(
                    f"Error using refresh_token for {user.name}: {e}. Requiring fresh login."
                )
                return False
            else:
                self.log.debug(
                    f"Received fresh access_token for {user.name} via refresh_token"
                )

            # refresh_token may not be returned when refreshing a token
            # in which case, keep the current one
            if not token_info.get("refresh_token"):
                token_info["refresh_token"] = refresh_token
            try:
                auth_model = await self._token_to_auth_model(token_info)
            except Exception as e:
                # this means we were issued a fresh access token,
                # but it didn't work! Fail harder?
                self.log.error(
                    f"Error refreshing auth with fresh access_token for {user.name}: {e}. Requiring fresh login."
                )
                return False

        # return False if auth_model is None for "needs new login"
        self.log.debug("post-refresh: %s", json.dumps(auth_model, indent=2))
        return auth_model or False

    def build_auth_state_dict(self, token_info, user_info):
        """
        Add workspaces claim to auth_state if present in user_info.
        """
        self.log.debug("Building auth_state dict...")
        self.log.debug("token_info: %s", json.dumps(token_info, indent=2))
        self.log.debug("user_info: %s", json.dumps(user_info, indent=2))
        auth_state = super().build_auth_state_dict(token_info, user_info)
        if "workspaces" in user_info:
            auth_state["workspaces"] = sorted(user_info["workspaces"])
            self.log.info(
                "Workspaces added to auth_state: %s", auth_state["workspaces"]
            )
        else:
            self.log.warning("No workspaces claim in user token info")
        return auth_state

    def exchange_token(self, subject_token: str, scope: list[str]) -> TokenInfo:
        """
        Exchange the subject_token for new credentials with different scope.
        """
        self.log.info("Exchanging token...")
        self.log.debug("Subject token: %s", subject_token)
        response = requests.post(
            self.token_url,
            headers=self.build_token_info_request_headers(),
            data={
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "grant_type": "urn:ietf:params:oauth:grant-type:token-exchange",
                "subject_token": subject_token,
                "scope": " ".join(scope),
            },
        )
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as exc:
            self.log.error("Token exchange failed: %s", exc)
            raise
        self.log.info("Token exchange successful")
        return response.json()
