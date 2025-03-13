import logging
from typing import Any, Optional

from oauthenticator.oauth2 import (
    OAuthCallbackHandler,
    OAuthenticator,
    OAuthLoginHandler,
    OAuthLogoutHandler,
)
from tornado.web import RequestHandler
from traitlets import Bool, CRegExp, Unicode

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)


class WorkspaceHandlerMixin:
    """
    Mixin to handle workspace authentication. Should be used with tornado.web.RequestHandler
    and tornado.auth.OAuth2Mixin, and have higher precedence.
    """

    def authorize_redirect(
        self,
        redirect_uri: Optional[str] = None,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        extra_params: Optional[dict[str, Any]] = None,
        scope: Optional[list[str]] = None,
        response_type: str = "code",
    ) -> None:
        """
        Inject workspace name into the redirect_uri and scope before calling the
        superclass authorize_redirect method.
        """
        if scope is None:
            scope = []

        self.authenticator: EODHAuthenticator
        workspace = self.authenticator.get_workspace(self.request.host)

        workspace_redirect_uri = redirect_uri.format(
            workspace=workspace
        )  # interpolate workspace in redirect_uri

        workspace_scope = f"workspace:{workspace}"
        if workspace_scope not in scope:
            scope.append(workspace_scope)  # Add workspace to the scope

        super().authorize_redirect(
            redirect_uri=workspace_redirect_uri,
            client_id=client_id,
            client_secret=client_secret,
            extra_params=extra_params,
            scope=scope,
            response_type=response_type,
        )


class EODHLoginHandler(WorkspaceHandlerMixin, OAuthLoginHandler):
    pass


class EODHCallbackHandler(WorkspaceHandlerMixin, OAuthCallbackHandler):
    pass


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
    workspace_pattern = CRegExp(config=True)

    login_handler = EODHLoginHandler
    logout_handler = EODHLogoutHandler
    callback_handler = EODHCallbackHandler

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

    def get_callback_url(self, handler: RequestHandler = None):
        """
        Get my OAuth redirect URL

        Check if the callback_url has a {workspace} placeholder and replace it with the
        workspace extracted from the handler's request host.

        Otherwise pass through to superclass.
        """
        if handler and "{workspace}" in self.oauth_callback_url:
            if workspace := self.get_workspace(handler.request.host):
                return self.oauth_callback_url.format(workspace=workspace)
        return super().get_callback_url(handler)
