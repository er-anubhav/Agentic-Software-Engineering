import hmac
import hashlib
from typing import Optional


class GitHubAppAuth:
    """
    GitHub App Authentication & Webhook Signature Validation Engine.
    """

    def __init__(self, webhook_secret: str = "default_secret", app_id: str = "12345"):
        self.webhook_secret = webhook_secret
        self.app_id = app_id

    def verify_signature(self, payload_body: bytes, signature_header: Optional[str]) -> bool:
        if not signature_header:
            return False

        if not signature_header.startswith("sha256="):
            return False

        expected_sig = hmac.new(
            self.webhook_secret.encode("utf-8"),
            payload_body,
            hashlib.sha256
        ).hexdigest()

        provided_sig = signature_header[7:]
        return hmac.compare_digest(expected_sig, provided_sig)

    def get_installation_token(self, repository: str) -> str:
        return f"ghs_fake_installation_token_for_{repository}"
