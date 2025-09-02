"""Monzoh - Python client for Monzo API."""

from .async_client import AsyncMonzoClient
from .auth import MonzoOAuth
from .client import MonzoClient
from .exceptions import (
    MonzoAuthenticationError,
    MonzoBadRequestError,
    MonzoError,
    MonzoNetworkError,
    MonzoNotFoundError,
    MonzoRateLimitError,
    MonzoServerError,
    MonzoValidationError,
)
from .models import (
    Account,
    Attachment,
    Balance,
    OAuthToken,
    Pot,
    Receipt,
    Transaction,
    Webhook,
    WhoAmI,
)
from .webhooks import (
    WebhookParseError,
    parse_transaction_webhook,
    parse_webhook_payload,
)

__version__ = "1.1.0"

__all__ = [
    # Main clients
    "MonzoClient",
    "AsyncMonzoClient",
    "MonzoOAuth",
    # Models
    "Account",
    "Balance",
    "Transaction",
    "Pot",
    "Attachment",
    "Receipt",
    "Webhook",
    "OAuthToken",
    "WhoAmI",
    # Exceptions
    "MonzoError",
    "MonzoAuthenticationError",
    "MonzoBadRequestError",
    "MonzoNotFoundError",
    "MonzoRateLimitError",
    "MonzoServerError",
    "MonzoNetworkError",
    "MonzoValidationError",
    # Webhook utilities
    "WebhookParseError",
    "parse_transaction_webhook",
    "parse_webhook_payload",
]
