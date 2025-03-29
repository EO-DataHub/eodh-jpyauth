# UK EO DataHub Jupyter Hub Authenticator

Custom JupyterHub classes to integrate JupyterHub with the UK EO DataHub.

Contains an EODHAuthenticator class to authenticate with the UK EO DataHub, as well as a custom KubeSpawner class to manage workspace scopes.

## Build

```bash
make build
```

## Publish

```bash
make publish token=$PYPI_TOKEN
```
