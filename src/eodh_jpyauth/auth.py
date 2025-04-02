from collections.abc import Iterable
from typing import TypedDict

import jwt
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

    def build_auth_state_dict(self, token_info, user_info):
        """
        Add workspaces claim to auth_state if present in user_info.
        """
        auth_state = super().build_auth_state_dict(token_info, user_info)

        # Decode claims from user OIDC access token
        try:
            claims = jwt.decode(
                token_info["access_token"], options={"verify_signature": False}
            )
        except KeyError as exc:
            self.log.error("No access_token in token_info: %r", exc)
            raise
        except jwt.exceptions.DecodeError as exc:
            self.log.error("Failed to decode token: %r", exc)
            raise

        # Use workspaces claim to populate auth_state
        if workspaces := claims.get("workspaces", None):
            if not isinstance(workspaces, Iterable):
                raise ValueError(
                    "Workspaces claim in user_info should be iterable. It is %s",
                    type(workspaces),
                )
            auth_state["workspaces"] = sorted(workspaces)
            self.log.info(
                "Workspaces added to auth_state: %s", auth_state["workspaces"]
            )
        else:
            self.log.warning(
                "No workspaces claim in user '%s' token info",
                user_info[self.username_claim],
            )
        return auth_state
