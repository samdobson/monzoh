"""Monzoh - Python client for Monzo API."""

from .auth import MonzoOAuth
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
from .main import MonzoClient
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

__version__ = "1.1.0"

__all__ = [
    # Main client
    "MonzoClient",
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
]
