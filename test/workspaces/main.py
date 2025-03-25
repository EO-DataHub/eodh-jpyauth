import logging
import os

import jwt
from fastapi import FastAPI, HTTPException, Request

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[logging.StreamHandler()],
)

ALLOWED_USERS = os.environ.get("ALLOWED_USERS", "").split(",")

app = FastAPI()


@app.middleware("http")
async def extract_oidc_claims(request: Request, call_next):
    logging.debug("oidc: %s", request.url)
    authorization: str = request.headers.get("Authorization")
    if authorization is None or not authorization.startswith("Bearer "):
        logging.debug("oidc: no or invalid authorization header")
        request.state.token = None
        request.state.claims = {}
    else:
        logging.debug("oidc: found valid authorization header")
        request.state.token = authorization.removeprefix("Bearer ")
        try:
            request.state.claims = jwt.decode(
                request.state.token, options={"verify_signature": False}
            )
            logging.debug("oidc: decoded claims: %s", request.state.claims)
        except jwt.exceptions.DecodeError:
            logging.error("oidc: failed to decode token")
            request.state.claims = {}

    response = await call_next(request)
    return response


@app.get("/api/workspaces")
async def get_workspaces(request: Request):
    logging.info("REQUEST: GET /api/workspaces")

    user = request.state.claims["preferred_username"]
    if user not in ALLOWED_USERS:
        logging.error("user %s forbidden", user)
        raise HTTPException(status_code=403, detail="Forbidden")

    return [
        {
            "name": "workspace1",
        },
        {
            "name": "workspace2",
        },
    ]
