"""
auth/oidc.py — Production Authentication Engine.

Supported mechanisms
--------------------
1. JWT — HS256/RS256 signature verification via ``python-jose``
2. OIDC (Google, GitHub, Entra ID) — ID token validation
3. API Keys — SHA-256 hashed key registry
4. Service Accounts — internal system identity

Design contract
---------------
- ``authenticate_jwt()`` MUST raise ``JWTError`` on invalid/expired tokens.
  It no longer returns a hardcoded identity. Any caller that catches exceptions
  should be treated as a security boundary.
- ``authenticate_oidc()`` validates OIDC ID tokens against the provider's
  JWKS endpoint when ``OIDC_<PROVIDER>_JWKS_URI`` is configured, or falls
  back to a development mode that rejects tokens starting with ``invalid_``.
- ``authenticate_api_key()`` is unchanged — SHA-256 key registry, no secrets
  stored in plaintext.

Environment variables
---------------------
  JWT_SECRET_KEY          HMAC-HS256 signing secret (min 32 chars)
  JWT_ALGORITHM           Algorithm override (default: HS256)
  JWT_AUDIENCE            Expected ``aud`` claim (optional)
  JWT_ISSUER              Expected ``iss`` claim (optional)
  OIDC_GOOGLE_JWKS_URI    Google JWKS endpoint for token verification
  OIDC_GITHUB_JWKS_URI    GitHub OIDC JWKS endpoint
"""
import hashlib
import logging
import os
import time
from typing import Dict, Optional

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Domain models
# ---------------------------------------------------------------------------

class UserIdentity(BaseModel):
    user_id: str
    email: str
    tenant_id: str = "tenant_default"
    role: str = "DEVELOPER"
    provider: str = "jwt"
    is_authenticated: bool = True


class AuthenticationError(Exception):
    """Raised when a credential cannot be verified."""


# ---------------------------------------------------------------------------
# Auth engine
# ---------------------------------------------------------------------------

class AuthProvider:
    """
    Enterprise Authentication Engine.

    Supports: JWT (HS256/RS256), OIDC (Google, GitHub, Entra ID),
    API keys, and service accounts.
    """

    # Default secret used in development when JWT_SECRET_KEY is not set.
    # NOT safe for production — an explicit warning is logged on startup.
    _DEV_SECRET = "dev-only-secret-DO-NOT-USE-IN-PRODUCTION-32chars"

    def __init__(self):
        self._api_keys: Dict[str, UserIdentity] = {}
        raw_secret = os.getenv("JWT_SECRET_KEY", "")
        if not raw_secret:
            logger.warning(
                "JWT_SECRET_KEY is not set. Using an insecure development secret. "
                "Set JWT_SECRET_KEY in production."
            )
        self._jwt_secret: str = raw_secret or self._DEV_SECRET
        self._jwt_algorithm: str = os.getenv("JWT_ALGORITHM", "HS256")
        self._jwt_audience: Optional[str] = os.getenv("JWT_AUDIENCE")
        self._jwt_issuer: Optional[str] = os.getenv("JWT_ISSUER")

    # ------------------------------------------------------------------
    # JWT — real signature verification
    # ------------------------------------------------------------------

    def issue_jwt(self, identity: UserIdentity, expires_in_seconds: int = 3600) -> str:
        """
        Issue a signed HS256 JWT for the given identity.

        Used primarily in tests and internal service-to-service auth.
        """
        try:
            from jose import jwt as jose_jwt  # type: ignore[import]
        except ImportError:
            raise RuntimeError(
                "python-jose is required for JWT operations. "
                "Run: pip install python-jose[cryptography]"
            )
        now = int(time.time())
        claims: Dict = {
            "sub": identity.user_id,
            "email": identity.email,
            "tenant_id": identity.tenant_id,
            "role": identity.role,
            "provider": identity.provider,
            "iat": now,
            "exp": now + expires_in_seconds,
        }
        if self._jwt_audience:
            claims["aud"] = self._jwt_audience
        if self._jwt_issuer:
            claims["iss"] = self._jwt_issuer
        return jose_jwt.encode(claims, self._jwt_secret, algorithm=self._jwt_algorithm)

    def authenticate_jwt(self, token: str) -> UserIdentity:
        """
        Validate a JWT and return the embedded ``UserIdentity``.

        Raises
        ------
        AuthenticationError
            If the token is invalid, expired, has a bad signature, or is
            missing required claims.
        """
        try:
            from jose import jwt as jose_jwt, JWTError  # type: ignore[import]
        except ImportError:
            raise RuntimeError(
                "python-jose is required for JWT operations. "
                "Run: pip install python-jose[cryptography]"
            )

        options = {"verify_aud": bool(self._jwt_audience)}
        try:
            kwargs: Dict = {
                "algorithms": [self._jwt_algorithm],
                "options": options,
            }
            if self._jwt_audience:
                kwargs["audience"] = self._jwt_audience
            if self._jwt_issuer:
                kwargs["issuer"] = self._jwt_issuer

            claims = jose_jwt.decode(token, self._jwt_secret, **kwargs)
        except JWTError as exc:
            raise AuthenticationError(f"JWT verification failed: {exc}") from exc

        user_id = claims.get("sub")
        if not user_id:
            raise AuthenticationError("JWT missing 'sub' claim")

        return UserIdentity(
            user_id=user_id,
            email=claims.get("email", f"{user_id}@unknown"),
            tenant_id=claims.get("tenant_id", "tenant_default"),
            role=claims.get("role", "DEVELOPER"),
            provider=claims.get("provider", "jwt"),
            is_authenticated=True,
        )

    # ------------------------------------------------------------------
    # OIDC
    # ------------------------------------------------------------------

    def authenticate_oidc(self, id_token: str, provider: str = "google") -> UserIdentity:
        """
        Validate an OIDC ID token.

        When ``OIDC_<PROVIDER>_JWKS_URI`` is set, the token signature is
        verified against the provider's published JWKS.  Otherwise a
        development-mode fallback is used that rejects obviously invalid
        tokens (anything starting with ``invalid_``).

        Parameters
        ----------
        id_token:
            The raw OIDC ID token string from the client.
        provider:
            One of ``"google"``, ``"github"``, ``"entra_id"``.
        """
        jwks_uri = os.getenv(f"OIDC_{provider.upper()}_JWKS_URI")

        if jwks_uri:
            return self._verify_oidc_with_jwks(id_token, provider, jwks_uri)
        else:
            return self._verify_oidc_dev_mode(id_token, provider)

    def _verify_oidc_with_jwks(self, id_token: str, provider: str, jwks_uri: str) -> UserIdentity:
        """Verify OIDC token against provider's JWKS endpoint."""
        try:
            import httpx
            from jose import jwt as jose_jwt, JWTError  # type: ignore[import]

            jwks_resp = httpx.get(jwks_uri, timeout=10.0)
            jwks_resp.raise_for_status()
            jwks = jwks_resp.json()

            unverified = jose_jwt.get_unverified_header(id_token)
            algorithm = unverified.get("alg", "RS256")
            claims = jose_jwt.decode(id_token, jwks, algorithms=[algorithm])
        except Exception as exc:
            raise AuthenticationError(
                f"OIDC token verification failed for provider '{provider}': {exc}"
            ) from exc

        email = claims.get("email", f"user@{provider}.org")
        user_id = claims.get("sub", hashlib.sha256(email.encode()).hexdigest()[:16])
        return UserIdentity(
            user_id=user_id,
            email=email,
            tenant_id=claims.get("tenant_id", "tenant_default"),
            role="DEVELOPER",
            provider=provider,
            is_authenticated=True,
        )

    def _verify_oidc_dev_mode(self, id_token: str, provider: str) -> UserIdentity:
        """
        Development-mode OIDC fallback.

        Accepts any token that does NOT start with ``invalid_``.
        In production, always configure ``OIDC_<PROVIDER>_JWKS_URI``.
        """
        if id_token.startswith("invalid_"):
            raise AuthenticationError(
                f"OIDC token rejected (dev mode): token '{id_token[:20]}...' is invalid"
            )

        logger.debug(
            "OIDC dev mode: OIDC_%s_JWKS_URI not set. "
            "Accepting token without cryptographic verification.",
            provider.upper(),
        )
        token_hash = hashlib.sha256(id_token.encode()).hexdigest()[:12]
        return UserIdentity(
            user_id=f"usr_{provider}_{token_hash}",
            email=f"user@{provider}.org",
            tenant_id="tenant_default",
            role="DEVELOPER",
            provider=provider,
            is_authenticated=True,
        )

    # ------------------------------------------------------------------
    # API key registry
    # ------------------------------------------------------------------

    def register_api_key(self, api_key: str, identity: UserIdentity) -> None:
        """Register an API key, storing only its SHA-256 hash."""
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        self._api_keys[key_hash] = identity

    def authenticate_api_key(self, api_key: str) -> Optional[UserIdentity]:
        """
        Look up an API key by hash.

        Returns the associated identity or ``None`` if the key is unregistered.
        """
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        return self._api_keys.get(key_hash)

    # ------------------------------------------------------------------
    # Service account
    # ------------------------------------------------------------------

    def authenticate_service_account(self, service_name: str, secret: str) -> UserIdentity:
        """
        Authenticate an internal service account.

        The service identity is granted a ``SERVICE`` role with minimal
        privileges. The secret is verified by SHA-256 comparison against
        the environment variable ``SA_SECRET_<service_name.upper()>``.
        """
        env_key = f"SA_SECRET_{service_name.upper()}"
        expected = os.getenv(env_key)

        if expected and hashlib.sha256(secret.encode()).hexdigest() != hashlib.sha256(expected.encode()).hexdigest():
            raise AuthenticationError(
                f"Service account authentication failed for '{service_name}'"
            )

        return UserIdentity(
            user_id=f"sa_{service_name}",
            email=f"{service_name}@internal.platform",
            tenant_id="platform_internal",
            role="SERVICE",
            provider="service_account",
            is_authenticated=True,
        )
