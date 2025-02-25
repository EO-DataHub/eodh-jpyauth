FROM quay.io/jupyterhub/jupyterhub:4.1.0

RUN python3 -m pip install --no-cache-dir \
    dockerspawner jupyterhub-nativeauthenticator

COPY src/jyk_auth /tmp/app/jyk_auth
COPY pyproject.toml README.md /tmp/app
RUN pip3 install -e /tmp/app
RUN rm -rf /tmp/app

CMD ["jupyterhub", "-f", "/srv/jupyterhub/jupyterhub_config.py"]
