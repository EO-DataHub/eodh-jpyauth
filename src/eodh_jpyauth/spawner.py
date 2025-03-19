from kubespawner.slugs import safe_slug
from kubespawner.spawner import KubeSpawner
from traitlets import Unicode


class EODHSpawner(KubeSpawner):
    workspace = Unicode(
        None,
        allow_none=False,
        config=True,
        help="The workspace of the notebook",
    )

    def _expand_user_properties(self, template, slug_scheme=None):
        """
        Expand user properties in template strings
        """
        safe_username = safe_slug(self.user.name)
        safe_workspace = safe_slug(self.workspace)
        servername = f"{safe_username}--{safe_workspace}"
        ns = dict(
            username=safe_slug(self.user.name),
            workspace=safe_slug(self.workspace),
            servername=servername,
            user_server=servername,
        )
        for attr_name in ("pod_name", "pvc_name", "namespace"):
            ns[attr_name] = getattr(self, attr_name, f"{attr_name}_unavailable!")
        return template.format(**ns)
