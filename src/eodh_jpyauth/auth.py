from collections.abc import Iterable
from functools import cached_property
from typing import Any, TypedDict

import jwt
from oauthenticator.oauth2 import OAuthenticator, OAuthLogoutHandler
from traitlets import Bool, List, Unicode, default


class TokenInfo(TypedDict):
    access_token: str
    expires_in: int
    refresh_token: str
    refresh_expires_in: int
    scope: str


class EODHLogoutHandler(OAuthLogoutHandler):
    """Log a user out by clearing both their JupyterHub login cookie and SSO cookie."""

    async def get(self) -> None:
        self.log.info("EODH Logout")
        assert self.authenticator is not None
        if self.authenticator.enable_logout:
            await self.default_handle_logout()
            await self.handle_logout()

            redirect_url = self.authenticator.oauth_logout_url
            if self.authenticator.oauth_logout_redirect_uri:
                redirect_url += f"?redirect_uri={self.authenticator.oauth_logout_redirect_uri}"

            self.redirect(redirect_url)
        else:
            await super().get()


class EODHAuthenticator(OAuthenticator):
    enable_logout = Bool(False, config=True)
    oauth_logout_url = Unicode(config=True)
    oauth_logout_redirect_uri = Unicode(config=True)

    jwks_url = Unicode(
        config=True,
        help="URL of the JWKS endpoint used to verify the access token's signature.",
    )
    jwt_audience = List(
        Unicode(),
        config=True,
        default_value=["eodh-workspaces"],
        help="Acceptable 'aud' values for the access token.",
    )

    logout_handler = EODHLogoutHandler

    @default("jwks_url")
    def _jwks_url_default(self) -> str:
        return self.token_url.rsplit("/", 1)[0] + "/certs"

    @cached_property
    def _jwks_client(self) -> jwt.PyJWKClient:
        return jwt.PyJWKClient(self.jwks_url)

    def build_auth_state_dict(self, token_info: Any, user_info: Any) -> dict[str, Any]:
        """
        Add workspaces claim to auth_state if present in user_info.
        """
        auth_state = super().build_auth_state_dict(token_info, user_info)

        # Decode and verify claims from user OIDC access token
        try:
            access_token = token_info["access_token"]
        except KeyError as exc:
            self.log.error("No access_token in token_info: %r", exc)
            raise
        try:
            signing_key = self._jwks_client.get_signing_key_from_jwt(access_token)
            claims = jwt.decode(
                access_token,
                signing_key.key,
                audience=self.jwt_audience,
                algorithms=["RS256"],
            )
        except jwt.PyJWTError as exc:
            self.log.error("Failed to verify token: %r", exc)
            raise

        # Use workspaces claim to populate auth_state
        if workspaces := claims.get("workspaces", None):
            if isinstance(workspaces, (str, bytes)) or not isinstance(workspaces, Iterable):
                raise ValueError(
                    "Workspaces claim in user_info should be iterable. It is %s",
                    type(workspaces),
                )
            auth_state["workspaces"] = sorted(workspaces)
            self.log.info("Workspaces added to auth_state: %s", auth_state["workspaces"])
        else:
            self.log.warning(
                "No workspaces claim in user '%s' token info",
                user_info[self.username_claim],
            )
        return auth_state
