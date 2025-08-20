"""Pydantic models for Monzo API entities."""

from datetime import datetime
from typing import Any, Literal, Optional, Union

from pydantic import BaseModel, Field, field_validator


class Account(BaseModel):
    """Represents a Monzo account."""

    id: str = Field(..., description="Unique account identifier")
    description: str = Field(..., description="Human-readable account description")
    created: datetime = Field(..., description="Account creation timestamp")
    closed: bool = Field(False, description="Whether the account is closed")


class AccountType(BaseModel):
    """Account type filter."""

    account_type: Literal["uk_retail", "uk_retail_joint"] = Field(
        ..., description="Type of account"
    )


class Balance(BaseModel):
    """Account balance information."""

    balance: int = Field(
        ...,
        description=(
            "Available balance in minor units of the currency, "
            "eg. pennies for GBP, or cents for EUR and USD"
        ),
    )
    total_balance: int = Field(
        ...,
        description=(
            "Total balance including pots in minor units of the currency, "
            "eg. pennies for GBP, or cents for EUR and USD"
        ),
    )
    currency: str = Field(..., description="ISO 4217 currency code")
    spend_today: int = Field(
        ...,
        description=(
            "Amount spent today in minor units of the currency, "
            "eg. pennies for GBP, or cents for EUR and USD"
        ),
    )


class Address(BaseModel):
    """Address information."""

    address: str = Field(..., description="Street address")
    city: str = Field(..., description="City name")
    country: str = Field(..., description="Country code (e.g., 'GB')")
    latitude: float = Field(..., description="Geographic latitude coordinate")
    longitude: float = Field(..., description="Geographic longitude coordinate")
    postcode: str = Field(..., description="Postal code")
    region: str = Field(..., description="Region or county name")


class Merchant(BaseModel):
    """Merchant information."""

    id: str = Field(..., description="Unique merchant identifier")
    name: str = Field(..., description="Merchant display name")
    category: str = Field(
        ..., description="Merchant category (e.g., 'eating_out', 'transport')"
    )
    created: datetime = Field(..., description="Merchant creation timestamp")
    group_id: str = Field(..., description="Merchant group identifier")
    logo: Optional[str] = Field(None, description="URL to merchant logo image")
    emoji: Optional[str] = Field(None, description="Emoji representing the merchant")
    address: Optional[Address] = Field(None, description="Merchant address information")


class Transaction(BaseModel):
    """Represents a transaction."""

    id: str = Field(..., description="Unique transaction identifier")
    amount: int = Field(
        ...,
        description=(
            "Amount in minor units of the currency, "
            "eg. pennies for GBP, or cents for EUR and USD (negative for debits)"
        ),
    )
    created: datetime = Field(..., description="Transaction creation timestamp")
    currency: str = Field(..., description="ISO 4217 currency code (e.g., 'GBP')")
    description: str = Field(
        ..., description="Transaction description from payment processor"
    )
    account_balance: Optional[int] = Field(
        None,
        description=(
            "Account balance after transaction in minor units of the currency, "
            "eg. pennies for GBP, or cents for EUR and USD"
        ),
    )
    category: Optional[str] = Field(
        None,
        description=(
            "Transaction category (e.g., 'eating_out', 'transport', 'groceries')"
        ),
    )
    is_load: bool = Field(False, description="Whether this is a top-up transaction")
    settled: Optional[datetime] = Field(
        None, description="Settlement timestamp (when transaction completed)"
    )
    merchant: Union[str, Merchant, None] = Field(
        None, description="Merchant ID or expanded merchant object"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Custom key-value metadata"
    )
    notes: Optional[str] = Field(
        None, description="User-added notes for the transaction"
    )
    decline_reason: Optional[
        Literal[
            "INSUFFICIENT_FUNDS",
            "CARD_INACTIVE",
            "CARD_BLOCKED",
            "INVALID_CVC",
            "OTHER",
            "STRONG_CUSTOMER_AUTHENTICATION_REQUIRED", # NB: Missing from docs
        ]
    ] = Field(
        None,
        description=(
            "Reason for transaction decline (only present on declined transactions)"
        ),
    )

    @field_validator("settled", mode="before")
    @classmethod
    def validate_settled(cls, v: Union[str, None]) -> Union[str, None]:
        """Convert empty strings to None for settled field."""
        if v == "":
            return None
        return v


class Pot(BaseModel):
    """Represents a pot."""

    id: str = Field(..., description="Unique pot identifier")
    name: str = Field(..., description="User-defined pot name")
    style: str = Field(
        ..., description="Pot visual style/theme (e.g., 'beach_ball', 'blue')"
    )
    balance: int = Field(
        ...,
        description=(
            "Pot balance in minor units of the currency, "
            "eg. pennies for GBP, or cents for EUR and USD"
        ),
    )
    currency: str = Field(..., description="ISO 4217 currency code")
    created: datetime = Field(..., description="Pot creation timestamp")
    updated: datetime = Field(..., description="Last pot update timestamp")
    deleted: bool = Field(False, description="Whether the pot is deleted")
    account_id: Optional[str] = Field(None, description="Associated account identifier")


class AttachmentUpload(BaseModel):
    """Upload attachment response."""

    file_url: str = Field(
        ..., description="URL where the file will be accessible after upload"
    )
    upload_url: str = Field(
        ..., description="Temporary URL to POST the file to for upload"
    )


class Attachment(BaseModel):
    """Represents an attachment."""

    id: str = Field(..., description="Unique attachment identifier")
    user_id: str = Field(..., description="ID of the user who owns the attachment")
    external_id: str = Field(
        ..., description="ID of the transaction the attachment is associated with"
    )
    file_url: str = Field(
        ..., description="URL where the attachment file is accessible"
    )
    file_type: str = Field(
        ..., description="MIME type of the attachment (e.g., 'image/png')"
    )
    created: datetime = Field(..., description="Attachment creation timestamp")


class FeedItemParams(BaseModel):
    """Feed item parameters."""

    title: str = Field(..., description="Title text to display in the feed item")
    image_url: str = Field(
        ..., description="URL of image to display (supports animated GIFs)"
    )
    body: Optional[str] = Field(
        None, description="Optional body text for the feed item"
    )
    background_color: Optional[str] = Field(
        None, description="Hex color for background (#RRGGBB format)"
    )
    title_color: Optional[str] = Field(
        None, description="Hex color for title text (#RRGGBB format)"
    )
    body_color: Optional[str] = Field(
        None, description="Hex color for body text (#RRGGBB format)"
    )


class ReceiptItem(BaseModel):
    """Receipt item."""

    description: str = Field(..., description="Description of the purchased product")
    amount: int = Field(
        ...,
        description=(
            "Amount in minor units of the currency, "
            "eg. pennies for GBP, or cents for EUR and USD"
        ),
    )
    currency: str = Field(..., description="ISO 4217 currency code")
    quantity: Optional[float] = Field(
        None, description="Quantity purchased (supports decimals for weights)"
    )
    unit: Optional[str] = Field(
        None, description="Unit of measurement (e.g., 'kg', 'pieces')"
    )
    tax: Optional[int] = Field(
        None,
        description=(
            "Tax amount in minor units of the currency, "
            "eg. pennies for GBP, or cents for EUR and USD"
        ),
    )
    sub_items: Optional[list["ReceiptItem"]] = Field(
        None, description="Sub-items (e.g., extras, modifications)"
    )


class ReceiptTax(BaseModel):
    """Receipt tax."""

    description: str = Field(..., description="Tax description (e.g., 'VAT')")
    amount: int = Field(
        ...,
        description=(
            "Tax amount in minor units of the currency, "
            "eg. pennies for GBP, or cents for EUR and USD"
        ),
    )
    currency: str = Field(..., description="ISO 4217 currency code")
    tax_number: Optional[str] = Field(None, description="Tax registration number")


class ReceiptPayment(BaseModel):
    """Receipt payment."""

    type: Literal["card", "cash", "gift_card"] = Field(
        ..., description="Payment method type"
    )
    amount: int = Field(
        ...,
        description=(
            "Payment amount in minor units of the currency, "
            "eg. pennies for GBP, or cents for EUR and USD"
        ),
    )
    currency: str = Field(..., description="ISO 4217 currency code")
    bin: Optional[str] = Field(
        None, description="Bank Identification Number (for card payments)"
    )
    last_four: Optional[str] = Field(
        None, description="Last four digits of card number"
    )
    auth_code: Optional[str] = Field(
        None, description="Authorisation code for card payment"
    )
    aid: Optional[str] = Field(None, description="Application Identifier")
    mid: Optional[str] = Field(None, description="Merchant Identifier")
    tid: Optional[str] = Field(None, description="Terminal Identifier")
    gift_card_type: Optional[str] = Field(
        None, description="Type of gift card (for gift card payments)"
    )


class ReceiptMerchant(BaseModel):
    """Receipt merchant information."""

    name: Optional[str] = Field(None, description="Merchant name")
    online: Optional[bool] = Field(
        None,
        description=(
            "Whether this is an online merchant (true) or physical store (false)"
        ),
    )
    phone: Optional[str] = Field(None, description="Merchant contact phone number")
    email: Optional[str] = Field(None, description="Merchant contact email address")
    store_name: Optional[str] = Field(
        None, description="Specific store name (e.g., 'Old Street')"
    )
    store_address: Optional[str] = Field(None, description="Physical store address")
    store_postcode: Optional[str] = Field(None, description="Store postcode")


class Receipt(BaseModel):
    """Represents a receipt."""

    id: Optional[str] = Field(
        None, description="Unique receipt identifier (generated by Monzo)"
    )
    external_id: str = Field(
        ..., description="External identifier (used as idempotency key)"
    )
    transaction_id: str = Field(..., description="ID of the associated transaction")
    total: int = Field(
        ...,
        description=(
            "Total amount in minor units of the currency, "
            "eg. pennies for GBP, or cents for EUR and USD"
        ),
    )
    currency: str = Field(..., description="ISO 4217 currency code")
    items: list[ReceiptItem] = Field(..., description="List of purchased items")
    taxes: Optional[list[ReceiptTax]] = Field(None, description="List of taxes applied")
    payments: Optional[list[ReceiptPayment]] = Field(
        None, description="List of payment methods used"
    )
    merchant: Optional[ReceiptMerchant] = Field(
        None, description="Merchant information for the receipt"
    )


class Webhook(BaseModel):
    """Represents a webhook."""

    id: str = Field(..., description="Unique webhook identifier")
    account_id: str = Field(..., description="Account to receive notifications for")
    url: str = Field(..., description="URL to send webhook notifications to")


class WebhookEvent(BaseModel):
    """Webhook event."""

    type: str = Field(..., description="Event type (e.g., 'transaction.created')")
    data: dict[str, Any] = Field(..., description="Event data payload")


class OAuthToken(BaseModel):
    """OAuth token response."""

    access_token: str = Field(..., description="Access token for API authentication")
    client_id: str = Field(..., description="Client identifier")
    expires_in: int = Field(..., description="Token expiry time in seconds")
    refresh_token: Optional[str] = Field(
        None, description="Refresh token (only for confidential clients)"
    )
    token_type: str = Field("Bearer", description="Token type (always 'Bearer')")
    user_id: str = Field(..., description="User identifier")


class WhoAmI(BaseModel):
    """Who am I response."""

    authenticated: bool = Field(..., description="Whether the request is authenticated")
    client_id: str = Field(..., description="Client identifier")
    user_id: str = Field(..., description="User identifier")


class PaginationParams(BaseModel):
    """Pagination parameters."""

    limit: Optional[int] = Field(
        None, ge=1, le=100, description="Number of results per page (1-100, default 30)"
    )
    since: Optional[Union[datetime, str]] = Field(
        None, description="Start time (RFC3339 timestamp) or object ID"
    )
    before: Optional[datetime] = Field(None, description="End time (RFC3339 timestamp)")


class ExpandParams(BaseModel):
    """Expand parameters."""

    expand: Optional[list[str]] = Field(
        None, description="List of related objects to expand inline"
    )


# Response containers
class AccountsResponse(BaseModel):
    """Accounts list response."""

    accounts: list[Account] = Field(..., description="List of user accounts")


class TransactionsResponse(BaseModel):
    """Transactions list response."""

    transactions: list[Transaction] = Field(..., description="List of transactions")


class TransactionResponse(BaseModel):
    """Single transaction response."""

    transaction: Transaction = Field(..., description="Single transaction object")


class PotsResponse(BaseModel):
    """Pots list response."""

    pots: list[Pot] = Field(..., description="List of user pots")


class AttachmentResponse(BaseModel):
    """Attachment response."""

    attachment: Attachment = Field(..., description="Attachment object")


class WebhooksResponse(BaseModel):
    """Webhooks list response."""

    webhooks: list[Webhook] = Field(..., description="List of registered webhooks")


class WebhookResponse(BaseModel):
    """Single webhook response."""

    webhook: Webhook = Field(..., description="Single webhook object")


class ReceiptResponse(BaseModel):
    """Receipt response."""

    receipt: Receipt = Field(..., description="Receipt object")


# Update forward references
ReceiptItem.model_rebuild()
