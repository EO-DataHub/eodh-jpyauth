FROM quay.io/jupyterhub/jupyterhub:4.1.0

RUN python3 -m pip install --no-cache-dir \
    dockerspawner jupyterhub-nativeauthenticator

COPY src/eodh_jpyauth /app/eodh_jpyauth
COPY pyproject.toml README.md /app
RUN pip3 install -e /app

CMD ["jupyterhub", "-f", "/srv/jupyterhub/jupyterhub_config.py"]
