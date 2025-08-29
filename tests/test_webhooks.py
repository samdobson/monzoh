"""Tests for webhook parsing functionality."""

import hashlib
import hmac
import json
from typing import Any

import pytest

from monzoh.webhooks import (
    TransactionWebhookPayload,
    WebhookParseError,
    WebhookPayload,
    WebhookSignatureError,
    parse_transaction_webhook,
    parse_webhook_payload,
    verify_webhook_signature,
)


class TestWebhookSignatureVerification:
    """Test webhook signature verification."""

    def test_verify_webhook_signature_valid(self) -> None:
        """Test signature verification with valid signature."""
        secret = "test_secret"
        body = b'{"type":"transaction.created","data":{"id":"tx_123"}}'

        # Generate valid signature
        signature = hmac.new(secret.encode("utf-8"), body, hashlib.sha1).hexdigest()

        assert verify_webhook_signature(body, signature, secret) is True

    def test_verify_webhook_signature_invalid(self) -> None:
        """Test signature verification with invalid signature."""
        secret = "test_secret"
        body = b'{"type":"transaction.created","data":{"id":"tx_123"}}'
        invalid_signature = "invalid_signature"

        assert verify_webhook_signature(body, invalid_signature, secret) is False

    def test_verify_webhook_signature_empty(self) -> None:
        """Test signature verification with empty signature."""
        secret = "test_secret"
        body = b'{"type":"transaction.created","data":{"id":"tx_123"}}'

        assert verify_webhook_signature(body, "", secret) is False

    def test_verify_webhook_signature_wrong_secret(self) -> None:
        """Test signature verification with wrong secret."""
        correct_secret = "correct_secret"
        wrong_secret = "wrong_secret"
        body = b'{"type":"transaction.created","data":{"id":"tx_123"}}'

        # Generate signature with correct secret
        signature = hmac.new(
            correct_secret.encode("utf-8"), body, hashlib.sha1
        ).hexdigest()

        # Verify with wrong secret should fail
        assert verify_webhook_signature(body, signature, wrong_secret) is False


class TestWebhookPayloadParsing:
    """Test webhook payload parsing."""

    @pytest.fixture
    def sample_transaction_payload(self) -> dict[str, Any]:
        """Sample transaction webhook payload."""
        return {
            "type": "transaction.created",
            "data": {
                "id": "tx_123456789",
                "amount": -450,
                "created": "2023-01-01T12:00:00Z",
                "currency": "GBP",
                "description": "Coffee Shop Purchase",
                "account_balance": 125000,
                "category": "eating_out",
                "is_load": False,
                "settled": "2023-01-01T12:00:00Z",
                "metadata": {},
                "notes": None,
                "decline_reason": None,
            },
        }

    @pytest.fixture
    def sample_balance_payload(self) -> dict[str, Any]:
        """Sample balance update webhook payload."""
        return {
            "type": "balance.updated",
            "data": {"account_id": "acc_123", "balance": 125000, "currency": "GBP"},
        }

    def test_parse_webhook_payload_transaction_without_signature(
        self, sample_transaction_payload: dict[str, Any]
    ) -> None:
        """Test parsing transaction webhook without signature verification."""
        body = json.dumps(sample_transaction_payload)
        headers: dict[str, str] = {}

        payload = parse_webhook_payload(
            body=body, headers=headers, verify_signature=False
        )

        assert isinstance(payload, TransactionWebhookPayload)
        assert payload.type == "transaction.created"
        assert payload.data.id == "tx_123456789"
        assert payload.data.amount == -450
        assert payload.data.description == "Coffee Shop Purchase"

    def test_parse_webhook_payload_transaction_with_valid_signature(
        self, sample_transaction_payload: dict[str, Any]
    ) -> None:
        """Test parsing transaction webhook with valid signature."""
        secret = "test_secret"
        body = json.dumps(sample_transaction_payload)
        body_bytes = body.encode("utf-8")

        # Generate valid signature
        signature = hmac.new(
            secret.encode("utf-8"), body_bytes, hashlib.sha1
        ).hexdigest()

        headers = {"X-Monzo-Signature": signature}

        payload = parse_webhook_payload(
            body=body, headers=headers, webhook_secret=secret, verify_signature=True
        )

        assert isinstance(payload, TransactionWebhookPayload)
        assert payload.type == "transaction.created"

    def test_parse_webhook_payload_bytes_input(
        self, sample_transaction_payload: dict[str, Any]
    ) -> None:
        """Test parsing webhook with bytes input."""
        body_bytes = json.dumps(sample_transaction_payload).encode("utf-8")
        headers: dict[str, str] = {}

        payload = parse_webhook_payload(
            body=body_bytes, headers=headers, verify_signature=False
        )

        assert isinstance(payload, TransactionWebhookPayload)
        assert payload.type == "transaction.created"

    def test_parse_webhook_payload_balance_update(
        self, sample_balance_payload: dict[str, Any]
    ) -> None:
        """Test parsing balance update webhook."""
        body = json.dumps(sample_balance_payload)
        headers: dict[str, str] = {}

        payload = parse_webhook_payload(
            body=body, headers=headers, verify_signature=False
        )

        assert isinstance(payload, WebhookPayload)
        assert payload.type == "balance.updated"
        assert "account_id" in payload.data

    def test_parse_webhook_payload_invalid_signature(
        self, sample_transaction_payload: dict[str, Any]
    ) -> None:
        """Test parsing webhook with invalid signature."""
        secret = "test_secret"
        body = json.dumps(sample_transaction_payload)
        headers = {"X-Monzo-Signature": "invalid_signature"}

        with pytest.raises(WebhookSignatureError, match="Invalid webhook signature"):
            parse_webhook_payload(
                body=body, headers=headers, webhook_secret=secret, verify_signature=True
            )

    def test_parse_webhook_payload_missing_secret(
        self, sample_transaction_payload: dict[str, Any]
    ) -> None:
        """Test parsing webhook with signature verification but missing secret."""
        body = json.dumps(sample_transaction_payload)
        headers: dict[str, str] = {}

        with pytest.raises(WebhookParseError, match="webhook_secret is required"):
            parse_webhook_payload(
                body=body, headers=headers, webhook_secret=None, verify_signature=True
            )

    def test_parse_webhook_payload_invalid_json(self) -> None:
        """Test parsing webhook with invalid JSON."""
        body = "invalid json"
        headers: dict[str, str] = {}

        with pytest.raises(WebhookParseError, match="Invalid JSON payload"):
            parse_webhook_payload(body=body, headers=headers, verify_signature=False)

    def test_parse_webhook_payload_missing_required_fields(self) -> None:
        """Test parsing webhook with missing required fields."""
        payload = {"type": "transaction.created"}  # Missing 'data' field
        body = json.dumps(payload)
        headers: dict[str, str] = {}

        with pytest.raises(
            WebhookParseError, match="Invalid webhook payload structure"
        ):
            parse_webhook_payload(body=body, headers=headers, verify_signature=False)

    def test_parse_webhook_payload_invalid_transaction_data(self) -> None:
        """Test parsing transaction webhook with invalid transaction data."""
        payload = {
            "type": "transaction.created",
            "data": {
                "id": "tx_123",
                # Missing required fields like amount, created, currency, description
            },
        }
        body = json.dumps(payload)
        headers: dict[str, str] = {}

        with pytest.raises(
            WebhookParseError, match="Invalid transaction webhook payload"
        ):
            parse_webhook_payload(body=body, headers=headers, verify_signature=False)


class TestTransactionWebhookParsing:
    """Test transaction-specific webhook parsing."""

    @pytest.fixture
    def sample_transaction_payload(self) -> dict[str, Any]:
        """Sample transaction webhook payload."""
        return {
            "type": "transaction.created",
            "data": {
                "id": "tx_123456789",
                "amount": -1250,
                "created": "2023-01-01T12:00:00Z",
                "currency": "GBP",
                "description": "Grocery Store",
                "account_balance": 98750,
                "category": "groceries",
                "is_load": False,
                "settled": "2023-01-01T12:00:00Z",
                "metadata": {"note": "Weekly shopping"},
                "notes": "Bought essentials",
                "decline_reason": None,
            },
        }

    def test_parse_transaction_webhook_success(
        self, sample_transaction_payload: dict[str, Any]
    ) -> None:
        """Test successful transaction webhook parsing."""
        body = json.dumps(sample_transaction_payload)
        headers: dict[str, str] = {}

        transaction = parse_transaction_webhook(
            body=body, headers=headers, verify_signature=False
        )

        assert transaction.id == "tx_123456789"
        assert transaction.amount == -1250
        assert transaction.description == "Grocery Store"
        assert transaction.category == "groceries"
        assert transaction.metadata == {"note": "Weekly shopping"}
        assert transaction.notes == "Bought essentials"

    def test_parse_transaction_webhook_with_signature(
        self, sample_transaction_payload: dict[str, Any]
    ) -> None:
        """Test transaction webhook parsing with signature verification."""
        secret = "webhook_secret_123"
        body = json.dumps(sample_transaction_payload)
        body_bytes = body.encode("utf-8")

        # Generate valid signature
        signature = hmac.new(
            secret.encode("utf-8"), body_bytes, hashlib.sha1
        ).hexdigest()

        headers = {"X-Monzo-Signature": signature}

        transaction = parse_transaction_webhook(
            body=body, headers=headers, webhook_secret=secret, verify_signature=True
        )

        assert transaction.id == "tx_123456789"
        assert transaction.amount == -1250

    def test_parse_transaction_webhook_wrong_event_type(self) -> None:
        """Test parsing transaction webhook with wrong event type."""
        payload = {
            "type": "balance.updated",
            "data": {"account_id": "acc_123", "balance": 125000},
        }
        body = json.dumps(payload)
        headers: dict[str, str] = {}

        with pytest.raises(
            WebhookParseError,
            match="Expected transaction.created event, got balance.updated",
        ):
            parse_transaction_webhook(
                body=body, headers=headers, verify_signature=False
            )

    def test_parse_transaction_webhook_invalid_signature(
        self, sample_transaction_payload: dict[str, Any]
    ) -> None:
        """Test transaction webhook parsing with invalid signature."""
        secret = "correct_secret"
        body = json.dumps(sample_transaction_payload)
        headers = {"X-Monzo-Signature": "invalid_signature"}

        with pytest.raises(WebhookSignatureError):
            parse_transaction_webhook(
                body=body, headers=headers, webhook_secret=secret, verify_signature=True
            )


class TestWebhookIntegration:
    """Integration tests for webhook functionality."""

    def test_complete_webhook_flow(self) -> None:
        """Test complete webhook processing flow."""
        # Simulate a real webhook payload from Monzo
        webhook_payload = {
            "type": "transaction.created",
            "data": {
                "id": "tx_000123456789abcdef",
                "amount": -750,  # £7.50 spending
                "created": "2023-12-01T10:30:00.000Z",
                "currency": "GBP",
                "description": "Local Coffee Shop",
                "account_balance": 42500,  # £425.00 remaining
                "category": "eating_out",
                "is_load": False,
                "settled": "2023-12-01T10:30:00.000Z",
                "metadata": {},
                "notes": None,
                "decline_reason": None,
                "merchant": None,
            },
        }

        # Webhook secret
        secret = "your_webhook_secret_here"

        # Serialize payload
        body = json.dumps(webhook_payload)
        body_bytes = body.encode("utf-8")

        # Generate signature (simulating Monzo's signature)
        signature = hmac.new(
            secret.encode("utf-8"), body_bytes, hashlib.sha1
        ).hexdigest()

        headers = {"X-Monzo-Signature": signature, "Content-Type": "application/json"}

        # Parse with full validation
        transaction = parse_transaction_webhook(
            body=body, headers=headers, webhook_secret=secret, verify_signature=True
        )

        # Verify transaction details
        assert transaction.id == "tx_000123456789abcdef"
        assert transaction.amount == -750
        assert transaction.description == "Local Coffee Shop"
        assert transaction.category == "eating_out"
        assert transaction.account_balance == 42500
        assert transaction.currency == "GBP"
        assert transaction.is_load is False

        # Verify amounts in pounds
        amount_pounds = abs(transaction.amount) / 100
        balance_pounds = transaction.account_balance / 100

        assert amount_pounds == 7.50
        assert balance_pounds == 425.00
