import string
from typing import TYPE_CHECKING, Any

from kubespawner.slugs import safe_slug, _is_valid_general, _alphanum_lower, _object_pattern
from kubespawner.spawner import KubeSpawner as KubeSpawner_
from traitlets import Unicode

if TYPE_CHECKING:
    pass

_alpha_lower_or_digit = tuple(string.ascii_lowercase + string.digits)


def _is_valid_eodh_workspace_name(workspace: str) -> bool:
    """
    Validate workspace name:
        - 1 to 60 chars
        - starts with [a-z0-9]
        - ends with [a-z0-9]
        - alphanumeric + hyphens
    """
    return _is_valid_general(
        workspace,
        starts_with=_alpha_lower_or_digit,
        ends_with=_alphanum_lower,
        pattern=_object_pattern,
        max_length=60,  # Kubernetes namespace max length is 63 but we are prepending 'ws-'
        min_length=1,
    )


class KubeSpawner(KubeSpawner_):
    workspace = Unicode(
        None,
        allow_none=True,
        config=True,
        help="The workspace the spawner should launch in",
    )

    async def load_user_options(self) -> None:
        """
        Apply the workspace from the user options, if present, and apply all overrides
        that support workspace template parameter.
        """
        if "workspace" in self.user_options:
            self.workspace = self.user_options["workspace"]
            overrides = dict(
                namespace=self._expand_user_properties(self.user_namespace_template),
                pod_name=self._expand_user_properties(self.pod_name_template),
                pvc_name=self._expand_user_properties(self.pvc_name_template),
            )
            self._apply_overrides(spawner_override=overrides)

        await super().load_user_options()

    def get_state(self) -> dict[str, Any]:
        """
        Add workspace to the state
        """
        state = super().get_state()
        state["workspace"] = self.workspace
        return state

    def get_env(self) -> dict[str, Any]:
        """
        Add workspace to the environment
        """
        env = super().get_env()
        env["WORKSPACE"] = self.workspace
        return env

    def load_state(self, state: dict[str, Any]) -> None:
        """
        Load workspace from state
        """
        super().load_state(state)
        self.workspace = state.get("workspace")

    def _options_from_form(self, formdata: dict[str, Any]) -> dict[str, Any]:
        """
        Add workspace to the user options from the form then call super method and
        return the merged options
        """
        user_options = dict(workspace=formdata.pop("workspace", [None])[0])
        if user_options["workspace"]:
            self.log.debug("Found workspace '%s' in form data", user_options["workspace"])
        # Merge with the user options from the form
        user_options |= super()._options_from_form(formdata)
        return user_options

    def _expand_user_properties(self, template: str, slug_scheme: str | None = None) -> str:
        """
        Expand user properties in template strings
        """
        safe_username = safe_slug(self.user.name)  # type: ignore
        safe_workspace = safe_slug(self.workspace or "")
        eodh_safe_workspace = safe_slug(self.workspace or "", is_valid=_is_valid_eodh_workspace_name)
        safe_servername = safe_slug(self.name or "")
        safe_userserver = f"{safe_username}--{safe_servername}" if safe_servername else safe_username
        ns = dict(
            username=safe_username,
            workspace=safe_workspace,
            eodh_safe_workspace=eodh_safe_workspace,
            servername=safe_servername,
            user_server=safe_userserver,
        )
        for attr_name in ("pod_name", "pvc_name", "namespace"):
            ns[attr_name] = getattr(self, attr_name, f"{attr_name}_unavailable!")
        return template.format(**ns)
