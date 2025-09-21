"""Webhook payload parsing and validation utilities."""

import json
from typing import Any, Literal

from pydantic import BaseModel, ValidationError

from .exceptions import MonzoValidationError
from .models import Transaction


class WebhookParseError(MonzoValidationError):
    """Error parsing webhook payload."""


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


def parse_webhook_payload(
    body: str | bytes,
) -> TransactionWebhookPayload | WebhookPayload:
    """Parse and validate incoming webhook payload.

    Args:
        body: Raw request body (string or bytes)

    Returns:
        Parsed webhook payload with validated data

    Raises:
        WebhookParseError: If payload parsing or validation fails

    Example:
        ```python
        from monzoh.webhooks import parse_webhook_payload

        payload = parse_webhook_payload(body=request_body)

        if isinstance(payload, TransactionWebhookPayload):
            transaction = payload.data
            print(
                f"New transaction: {transaction.description} - "
                f"£{transaction.amount/100:.2f}"
            )
        ```
    """
    try:
        if isinstance(body, bytes):
            payload_data = json.loads(body.decode("utf-8"))
        else:
            payload_data = json.loads(body)
    except json.JSONDecodeError as e:
        msg = f"Invalid JSON payload: {e}"
        raise WebhookParseError(msg) from e

    try:
        base_payload = WebhookPayload(**payload_data)
    except ValidationError as e:
        msg = f"Invalid webhook payload structure: {e}"
        raise WebhookParseError(msg) from e

    event_type = base_payload.type

    if event_type == "transaction.created":
        try:
            return TransactionWebhookPayload(**payload_data)
        except ValidationError as e:
            msg = f"Invalid transaction webhook payload: {e}"
            raise WebhookParseError(msg) from e

    return base_payload


def parse_transaction_webhook(
    body: str | bytes,
) -> Transaction:
    """Parse webhook payload and return Transaction object directly.

    Convenience function that parses a transaction.created webhook
    and returns the Transaction object directly.

    Args:
        body: Raw request body (string or bytes)

    Returns:
        Validated Transaction object

    Raises:
        WebhookParseError: If payload is not a transaction.created event
            or validation fails

    Example:
        ```python
        from monzoh.webhooks import parse_transaction_webhook

        transaction = parse_transaction_webhook(body=request_body)

        print(f"New transaction: {transaction.description}")
        print(f"Amount: £{transaction.amount/100:.2f}")
        print(f"Category: {transaction.category}")
        ```
    """
    payload = parse_webhook_payload(body=body)

    if not isinstance(payload, TransactionWebhookPayload):
        msg = f"Expected transaction.created event, got {payload.type}"
        raise WebhookParseError(msg)

    return payload.data
