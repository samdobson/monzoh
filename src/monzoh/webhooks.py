"""Webhook payload parsing and validation utilities."""

import hashlib
import hmac
import json
from typing import Any, Literal

from pydantic import BaseModel, ValidationError

from .exceptions import MonzoValidationError
from .models import Transaction


class WebhookParseError(MonzoValidationError):
    """Error parsing webhook payload."""


class WebhookSignatureError(MonzoValidationError):
    """Invalid webhook signature."""


class WebhookPayload(BaseModel):
    """Base webhook payload structure."""

    type: str
    data: dict[str, Any]


class TransactionWebhookPayload(BaseModel):
    """Transaction-specific webhook payload."""

    type: Literal["transaction.created"]
    data: Transaction


class BalanceWebhookPayload(BaseModel):
    """Balance update webhook payload."""

    type: Literal["balance.updated"]
    data: dict[str, Any]


def verify_webhook_signature(body: bytes, signature: str, secret: str) -> bool:
    """Verify webhook signature using HMAC-SHA1.

    Args:
        body: Raw request body bytes
        signature: Signature from webhook headers (typically X-Monzo-Signature)
        secret: Your webhook secret key

    Returns:
        True if signature is valid, False otherwise

    Example:
        ```python
        from monzoh.webhooks import verify_webhook_signature

        # In your webhook handler
        body = await request.body()
        signature = request.headers.get("X-Monzo-Signature", "")

        if not verify_webhook_signature(body, signature, webhook_secret):
            raise HTTPException(status_code=403, detail="Invalid signature")
        ```
    """
    if not signature:
        return False

    expected_signature = hmac.new(
        secret.encode("utf-8"), body, hashlib.sha1
    ).hexdigest()

    return hmac.compare_digest(signature, expected_signature)


def parse_webhook_payload(
    body: str | bytes,
    headers: dict[str, str],
    webhook_secret: str | None = None,
    verify_signature: bool = True,
) -> TransactionWebhookPayload | WebhookPayload:
    """Parse and validate incoming webhook payload.

    Args:
        body: Raw request body (string or bytes)
        headers: Request headers dictionary
        webhook_secret: Webhook secret for signature verification
            (required if verify_signature=True)
        verify_signature: Whether to verify the webhook signature

    Returns:
        Parsed webhook payload with validated data

    Raises:
        WebhookSignatureError: If signature verification fails
        WebhookParseError: If payload parsing or validation fails

    Example:
        ```python
        from monzoh.webhooks import parse_webhook_payload

        # Basic usage without signature verification
        payload = parse_webhook_payload(
            body=request_body,
            headers=request_headers,
            verify_signature=False
        )

        if isinstance(payload, TransactionWebhookPayload):
            transaction = payload.data
            print(
                f"New transaction: {transaction.description} - "
                f"£{transaction.amount/100:.2f}"
            )

        # With signature verification
        payload = parse_webhook_payload(
            body=request_body,
            headers=request_headers,
            webhook_secret="your_webhook_secret"
        )
        ```
    """
    # Convert body to bytes if needed
    if isinstance(body, str):
        body_bytes = body.encode("utf-8")
    else:
        body_bytes = body

    # Verify signature if requested
    if verify_signature:
        if webhook_secret is None:
            raise WebhookParseError(
                "webhook_secret is required when verify_signature=True"
            )

        signature = headers.get("X-Monzo-Signature", "")
        if not verify_webhook_signature(body_bytes, signature, webhook_secret):
            raise WebhookSignatureError("Invalid webhook signature")

    # Parse JSON payload
    try:
        if isinstance(body, bytes):
            payload_data = json.loads(body.decode("utf-8"))
        else:
            payload_data = json.loads(body)
    except json.JSONDecodeError as e:
        raise WebhookParseError(f"Invalid JSON payload: {e}")

    # Validate basic payload structure
    try:
        base_payload = WebhookPayload(**payload_data)
    except ValidationError as e:
        raise WebhookParseError(f"Invalid webhook payload structure: {e}")

    # Parse specific event types with stronger validation
    event_type = base_payload.type

    if event_type == "transaction.created":
        try:
            return TransactionWebhookPayload(**payload_data)
        except ValidationError as e:
            raise WebhookParseError(f"Invalid transaction webhook payload: {e}")

    # Return generic payload for other event types
    return base_payload


def parse_transaction_webhook(
    body: str | bytes,
    headers: dict[str, str],
    webhook_secret: str | None = None,
    verify_signature: bool = True,
) -> Transaction:
    """Parse webhook payload and return Transaction object directly.

    Convenience function that parses a transaction.created webhook
    and returns the Transaction object directly.

    Args:
        body: Raw request body (string or bytes)
        headers: Request headers dictionary
        webhook_secret: Webhook secret for signature verification
        verify_signature: Whether to verify the webhook signature

    Returns:
        Validated Transaction object

    Raises:
        WebhookSignatureError: If signature verification fails
        WebhookParseError: If payload is not a transaction.created event
            or validation fails

    Example:
        ```python
        from monzoh.webhooks import parse_transaction_webhook

        # Parse transaction directly
        transaction = parse_transaction_webhook(
            body=request_body,
            headers=request_headers,
            webhook_secret="your_secret"
        )

        print(f"New transaction: {transaction.description}")
        print(f"Amount: £{transaction.amount/100:.2f}")
        print(f"Category: {transaction.category}")
        ```
    """
    payload = parse_webhook_payload(
        body=body,
        headers=headers,
        webhook_secret=webhook_secret,
        verify_signature=verify_signature,
    )

    if not isinstance(payload, TransactionWebhookPayload):
        raise WebhookParseError(
            f"Expected transaction.created event, got {payload.type}"
        )

    return payload.data
