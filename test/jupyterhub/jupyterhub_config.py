# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

# Configuration file for JupyterHub
import os

c = get_config()  # noqa: F821

# We rely on environment variables to configure JupyterHub so that we
# avoid having to rebuild the JupyterHub container every time we change a
# configuration parameter.

# Spawn single-user servers as Docker containers
c.JupyterHub.spawner_class = "dockerspawner.DockerSpawner"

# Spawn containers from this image
c.DockerSpawner.image = os.environ["DOCKER_NOTEBOOK_IMAGE"]

# Connect containers to this Docker network
network_name = os.environ["DOCKER_NETWORK_NAME"]
c.DockerSpawner.use_internal_ip = True
c.DockerSpawner.network_name = network_name

# Explicitly set notebook directory because we'll be mounting a volume to it.
# Most `jupyter/docker-stacks` *-notebook images run the Notebook server as
# user `jovyan`, and set the notebook directory to `/home/jovyan/work`.
# We follow the same convention.
notebook_dir = os.environ.get("DOCKER_NOTEBOOK_DIR", "/home/jovyan/work")
c.DockerSpawner.notebook_dir = notebook_dir

# Mount the real user's Docker volume on the host to the notebook user's
# notebook directory in the container
c.DockerSpawner.volumes = {"jupyterhub-user-{username}": notebook_dir}

# Remove containers once they are stopped
c.DockerSpawner.remove = True

# For debugging arguments passed to spawned containers
c.DockerSpawner.debug = True

# User containers will access hub by container name on the Docker network
c.JupyterHub.hub_ip = "jupyterhub"
c.JupyterHub.hub_port = 8080

# Persist hub data on volume mounted inside container
c.JupyterHub.cookie_secret_file = "/data/jupyterhub_cookie_secret"
c.JupyterHub.db_url = "sqlite:////data/jupyterhub.sqlite"

# Allow all signed-up users to login
c.Authenticator.allow_all = True
c.Authenticator.auto_login = True
c.Authenticator.enable_auth_state = True

print("Configuring JupyterHub...")
c.JupyterHub.authenticator_class = "eodh_jpyauth.auth.EODHAuthenticator"
c.JupyterHub.allow_named_servers = True
c.JupyterHub.template_paths = ["/app/templates"]

print("Configuring EODH Authenticator...")
c.EODHAuthenticator.client_id = os.environ["OAUTH_CLIENT_ID"]
c.EODHAuthenticator.client_secret = os.environ["OAUTH_CLIENT_SECRET"]
c.EODHAuthenticator.authorize_url = os.environ["OAUTH_AUTHORIZE_URL"]
c.EODHAuthenticator.token_url = os.environ["OAUTH_TOKEN_URL"]
c.EODHAuthenticator.oauth_callback_url = os.environ["OAUTH_CALLBACK_URL"]
c.EODHAuthenticator.userdata_url = os.environ["OAUTH_USERDATA_URL"]
c.EODHAuthenticator.username_claim = os.environ.get(
    "OAUTH_USERNAME_CLAIM", "preferred_username"
)
c.EODHAuthenticator.scope = ["openid workspaces"]
c.EODHAuthenticator.enable_logout = True
c.EODHAuthenticator.oauth_logout_url = os.environ["OAUTH_LOGOUT_URL"]
c.EODHAuthenticator.oauth_logout_redirect_uri = os.environ["OAUTH_LOGOUT_REDIRECT_URI"]

print("Configuring DockerSpawner...")
c.DockerSpawner.allowed_images = {
    "EO DataHub": "public.ecr.aws/eodh/eodh-default-notebook",
    "Python 3.12": "quay.io/jupyter/base-notebook:python-3.12",
    "R 4.4": "quay.io/jupyter/r-notebook:r-4.4.2",
}
