from oauthenticator.oauth2 import OAuthenticator, OAuthLogoutHandler
from traitlets import Bool, Unicode


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
        if "workspaces" in user_info:
            auth_state["workspaces"] = user_info["workspaces"]
            self.log.info(
                "Workspaces added to auth_state: %s", auth_state["workspaces"]
            )
        else:
            self.log.warning("No workspaces claim in user token info")
        return auth_state
