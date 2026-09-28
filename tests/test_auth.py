"""Tests for EODHAuthenticator.build_auth_state_dict's signature verification.

The access token's `workspaces` claim ends up gating which Kubernetes namespace a user's
notebook spawns into (see KubeSpawner.load_user_options), so a bug here that lets an
unverified/forged token through lets an attacker put arbitrary workspaces in their own
auth_state and spawn into someone else's workspace.

There is no private key for the real Keycloak instance, so these sign with a throwaway RSA
keypair and stub out the authenticator's JWKS client rather than calling the real endpoint.
"""

import types

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey
from jwt.utils import base64url_encode

from eodh_jpyauth.auth import EODHAuthenticator

PRIVATE_KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)


def _authenticator() -> EODHAuthenticator:
    authenticator = EODHAuthenticator()
    # cached_property: assigning directly overrides the descriptor's lazy lookup.
    authenticator._jwks_client = types.SimpleNamespace(  # type: ignore[attr-defined]
        get_signing_key_from_jwt=lambda token: types.SimpleNamespace(key=PRIVATE_KEY.public_key())
    )
    return authenticator


def _access_token(key: RSAPrivateKey, aud: str = "eodh-workspaces", **claims: object) -> str:
    return jwt.encode({"sub": "test-user", "aud": aud, **claims}, key, algorithm="RS256")


def test_workspaces_claim_from_a_genuinely_signed_token_is_added_to_auth_state() -> None:
    authenticator = _authenticator()
    token_info = {"access_token": _access_token(PRIVATE_KEY, workspaces=["ws-b", "ws-a"])}

    auth_state = authenticator.build_auth_state_dict(token_info, {})

    assert auth_state["workspaces"] == ["ws-a", "ws-b"]


def test_a_forged_signature_is_rejected() -> None:
    """This is the exact bug that shipped: verify_signature was False, so any signature -
    including one that is not cryptographically valid at all - was accepted.
    """
    header = base64url_encode(b'{"alg":"RS256","typ":"JWT"}').decode()
    payload = base64url_encode(
        b'{"sub":"attacker","workspaces":["someone-elses-workspace"],"aud":"eodh-workspaces"}'
    ).decode()
    forged_signature = base64url_encode(b"not-a-real-signature").decode()
    forged_token = f"{header}.{payload}.{forged_signature}"
    authenticator = _authenticator()

    with pytest.raises(jwt.PyJWTError):
        authenticator.build_auth_state_dict({"access_token": forged_token}, {})


def test_a_token_signed_by_a_different_key_is_rejected() -> None:
    """Guards against accepting any valid-looking signature rather than specifically
    Keycloak's: a token signed end-to-end correctly, just with the wrong key.
    """
    other_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    authenticator = _authenticator()
    token_info = {"access_token": _access_token(other_key, workspaces=["ws-a"])}

    with pytest.raises(jwt.PyJWTError):
        authenticator.build_auth_state_dict(token_info, {})


def test_the_wrong_audience_is_rejected() -> None:
    """A genuinely signed token issued for a different client should not be accepted here."""
    authenticator = _authenticator()
    token_info = {"access_token": _access_token(PRIVATE_KEY, aud="some-other-client", workspaces=["ws-a"])}

    with pytest.raises(jwt.PyJWTError):
        authenticator.build_auth_state_dict(token_info, {})


def test_missing_access_token_raises_key_error() -> None:
    authenticator = _authenticator()

    with pytest.raises(KeyError):
        authenticator.build_auth_state_dict({}, {})
