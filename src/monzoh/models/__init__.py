"""Pydantic models for Monzo API entities."""

# Import all models to maintain backward compatibility
from .accounts import Account, AccountsResponse, AccountType, Balance
from .attachments import Attachment, AttachmentResponse, AttachmentUpload
from .base import ExpandParams, OAuthToken, PaginationParams, WhoAmI
from .feed import FeedItemParams
from .pots import Pot, PotsResponse
from .receipts import (
    Receipt,
    ReceiptItem,
    ReceiptMerchant,
    ReceiptPayment,
    ReceiptResponse,
    ReceiptTax,
)
from .transactions import (
    Address,
    Merchant,
    Transaction,
    TransactionResponse,
    TransactionsResponse,
)
from .webhooks import Webhook, WebhookEvent, WebhookResponse, WebhooksResponse

__all__ = [
    # Base models
    "OAuthToken",
    "WhoAmI",
    "PaginationParams",
    "ExpandParams",
    # Account models
    "Account",
    "AccountType",
    "Balance",
    "AccountsResponse",
    # Transaction models
    "Transaction",
    "Merchant",
    "Address",
    "TransactionsResponse",
    "TransactionResponse",
    # Pot models
    "Pot",
    "PotsResponse",
    # Attachment models
    "Attachment",
    "AttachmentUpload",
    "AttachmentResponse",
    # Feed models
    "FeedItemParams",
    # Receipt models
    "Receipt",
    "ReceiptItem",
    "ReceiptTax",
    "ReceiptPayment",
    "ReceiptMerchant",
    "ReceiptResponse",
    # Webhook models
    "Webhook",
    "WebhookEvent",
    "WebhooksResponse",
    "WebhookResponse",
]
