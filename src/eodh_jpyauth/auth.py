from oauthenticator.oauth2 import OAuthenticator, OAuthLogoutHandler
from tornado.web import RequestHandler
from traitlets import Bool, CRegExp, Unicode


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
    workspace_pattern = CRegExp(config=True)

    logout_handler = EODHLogoutHandler

    def get_workspace(self, host: str) -> str | None:
        """
        Use authenticator configured compiled regex to extract workspaces from the
        login request host.
        """
        self.log.info("host %s", host)
        matches = self.workspace_pattern.match(host)
        if matches:
            return matches.group("workspace")
        else:
            return None

    def get_callback_url(self, handler: RequestHandler = None) -> str:
        """
        Get my OAuth redirect URL

        Check if the callback_url has a {workspace} placeholder and replace it with the
        workspace extracted from the handler's request host.

        Otherwise pass through to superclass.
        """
        if handler and "{host}" in self.oauth_callback_url:
            return self.oauth_callback_url.format(host=handler.request.host)
        return super().get_callback_url(handler)
