"""
Signed, time-limited tokens that let a client view a specific order via a
URL (e.g. sent by email) without logging in.

Deliberately NOT usable for API authentication: this token has its own
token_type ("order_link") and is signed with a secret isolated from
SIMPLE_JWT's global signing key, so
rest_framework_simplejwt.authentication.JWTAuthentication will never accept
it as a Bearer access token.
"""
from datetime import timedelta
from urllib.parse import urlencode

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.utils import timezone
from rest_framework_simplejwt.backends import TokenBackend
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import Token


class InvalidOrderLinkToken(Exception):
    """Token missing, malformed, expired, wrong type, or not valid for the given order."""


class OrderClaim:
    def __init__(self, client_id, order_id):
        self.client_id = client_id
        self.order_id = order_id


class OrderLinkGenerator(Token):
    token_type = "order_link"
    lifetime = timedelta(hours=72)  # fallback only; build_url() always sets an explicit exp

    _order_link_backend = None

    @property
    def token_backend(self) -> TokenBackend:
        """
        Overrides Token.token_backend to sign/verify with a secret dedicated
        to order-view links, isolated from SIMPLE_JWT's signing key (used
        for API access/refresh tokens).
        """
        cls = type(self)
        if cls._order_link_backend is None:
            secret = getattr(settings, "ORDER_LINK_SECRET_KEY", None)
            if not secret:
                raise ImproperlyConfigured(
                    "settings.ORDER_LINK_SECRET_KEY must be set to issue/verify order view links"
                )
            cls._order_link_backend = TokenBackend(
                algorithm="HS256", signing_key=secret, verifying_key=secret
            )
        return cls._order_link_backend

    @classmethod
    def build_url(cls, url_path, client, order, due_to):
        """
        Build the full "view order" URL: url_path with a signed token appended
        as a query parameter. due_to must be a timezone-aware future datetime.
        """
        if timezone.is_naive(due_to):
            raise ValueError("due_to must be timezone-aware")

        now = timezone.now()
        if due_to <= now:
            raise ValueError("due_to must be in the future")

        token = cls()
        token.set_exp(from_time=now, lifetime=due_to - now)
        token["client_id"] = client.id
        token["order_id"] = order.id

        separator = "&" if "?" in url_path else "?"
        return f"{url_path}{separator}{urlencode({'hash': str(token)})}"

    @classmethod
    def verify_for_order(cls, raw_token: str) -> OrderClaim:
        """
        Decode and fully validate raw_token (signature, expiry, token_type),
        then confirm it authorizes access to `order` specifically. Raises
        InvalidOrderLinkToken on any failure.
        :return OrderClaim
        """
        try:
            token = cls(raw_token)
        except TokenError as exc:
            raise InvalidOrderLinkToken(str(exc)) from exc

        try:
            return OrderClaim(token["client_id"], token["order_id"])
        except KeyError as exc:
            raise InvalidOrderLinkToken(f"Token missing required claim: {exc}") from exc