FROM quay.io/jupyterhub/jupyterhub:$JUPYTERHUB_VERSION

ARG JUPYTERHUB_VERSION

RUN python3 -m pip install --no-cache-dir \
    dockerspawner \
    jupyterhub-nativeauthenticator

WORKDIR /app
COPY src/eodh_jpyauth .
RUN pip3 install -r eodh_jpyauth

CMD ["jupyterhub", "-f", "/srv/jupyterhub/jupyterhub_config.py"]
