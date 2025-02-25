FROM quay.io/jupyterhub/jupyterhub:$JUPYTERHUB_VERSION

ARG JUPYTERHUB_VERSION

RUN python3 -m pip install --no-cache-dir \
    dockerspawner \
    jupyterhub-nativeauthenticator

WORKDIR /app
COPY src/jyk_auth .
RUN pip3 install -r jyk_auth

CMD ["jupyterhub", "-f", "/srv/jupyterhub/jupyterhub_config.py"]
