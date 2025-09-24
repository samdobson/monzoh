"""Tests for webhook parsing functionality."""

import json
from typing import Any, Literal, cast

import pytest
from pydantic_core import ValidationError

from monzoh.models import Transaction
from monzoh.webhooks import (
    TransactionWebhookPayload,
    WebhookParseError,
    WebhookPayload,
    parse_transaction_webhook,
    parse_webhook_payload,
)


class TestWebhookPayloadParsing:
    """Test webhook payload parsing."""

    @pytest.fixture
    def sample_transaction_payload(self) -> dict[str, Any]:
        """Sample transaction webhook payload.

        Returns:
            Dictionary containing sample transaction webhook payload.
        """
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
        """Sample balance update webhook payload.

        Returns:
            Dictionary containing sample balance update webhook payload.
        """
        return {
            "type": "balance.updated",
            "data": {"account_id": "acc_123", "balance": 125000, "currency": "GBP"},
        }

    def test_parse_webhook_payload_transaction(
        self, sample_transaction_payload: dict[str, Any]
    ) -> None:
        """Test parsing transaction webhook.

        Args:
            sample_transaction_payload: Sample transaction payload fixture.
        """
        body = json.dumps(sample_transaction_payload)

        payload = parse_webhook_payload(body=body)

        assert isinstance(payload, TransactionWebhookPayload)
        assert payload.type == "transaction.created"
        assert payload.data.id == "tx_123456789"
        assert payload.data.amount == -450
        assert payload.data.description == "Coffee Shop Purchase"

    def test_parse_webhook_payload_bytes_input(
        self, sample_transaction_payload: dict[str, Any]
    ) -> None:
        """Test parsing webhook with bytes input.

        Args:
            sample_transaction_payload: Sample transaction payload fixture.
        """
        body_bytes = json.dumps(sample_transaction_payload).encode("utf-8")

        payload = parse_webhook_payload(body=body_bytes)

        assert isinstance(payload, TransactionWebhookPayload)
        assert payload.type == "transaction.created"

    def test_parse_webhook_payload_balance_update(
        self, sample_balance_payload: dict[str, Any]
    ) -> None:
        """Test parsing balance update webhook.

        Args:
            sample_balance_payload: Sample balance payload fixture.
        """
        body = json.dumps(sample_balance_payload)

        payload = parse_webhook_payload(body=body)

        assert isinstance(payload, WebhookPayload)
        assert payload.type == "balance.updated"
        assert "account_id" in payload.data

    def test_parse_webhook_payload_invalid_json(self) -> None:
        """Test parsing webhook with invalid JSON."""
        body = "invalid json"

        with pytest.raises(WebhookParseError, match="Invalid JSON payload"):
            parse_webhook_payload(body=body)

    def test_parse_webhook_payload_missing_required_fields(self) -> None:
        """Test parsing webhook with missing required fields."""
        payload = {"type": "transaction.created"}
        body = json.dumps(payload)

        with pytest.raises(
            WebhookParseError, match="Invalid webhook payload structure"
        ):
            parse_webhook_payload(body=body)

    def test_parse_webhook_payload_invalid_transaction_data(self) -> None:
        """Test parsing transaction webhook with invalid transaction data."""
        payload = {
            "type": "transaction.created",
            "data": {
                "id": "tx_123",
            },
        }
        body = json.dumps(payload)

        with pytest.raises(
            WebhookParseError, match="Invalid transaction webhook payload"
        ):
            parse_webhook_payload(body=body)


class TestTransactionWebhookParsing:
    """Test transaction-specific webhook parsing."""

    @pytest.fixture
    def sample_transaction_payload(self) -> dict[str, Any]:
        """Sample transaction webhook payload.

        Returns:
            Dictionary containing sample transaction webhook payload.
        """
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
        """Test successful transaction webhook parsing.

        Args:
            sample_transaction_payload: Sample transaction payload fixture.
        """
        body = json.dumps(sample_transaction_payload)

        transaction = parse_transaction_webhook(body=body)

        assert transaction.id == "tx_123456789"
        assert transaction.amount == -1250
        assert transaction.description == "Grocery Store"
        assert transaction.category == "groceries"
        assert transaction.metadata == {"note": "Weekly shopping"}
        assert transaction.notes == "Bought essentials"

    def test_parse_transaction_webhook_wrong_event_type(self) -> None:
        """Test parsing transaction webhook with wrong event type."""
        payload = {
            "type": "balance.updated",
            "data": {"account_id": "acc_123", "balance": 125000},
        }
        body = json.dumps(payload)

        with pytest.raises(
            WebhookParseError,
            match="Expected transaction.created event, got balance.updated",
        ):
            parse_transaction_webhook(body=body)

    def test_parse_transaction_webhook_invalid_transaction_data(self) -> None:
        """Test parsing transaction webhook with invalid data."""
        payload = {
            "type": "transaction.created",
            "data": {
                "id": "tx_123",
            },
        }
        body = json.dumps(payload)

        with pytest.raises(WebhookParseError):
            parse_transaction_webhook(body=body)

    def test_parse_transaction_webhook_bytes_input(
        self, sample_transaction_payload: dict[str, Any]
    ) -> None:
        """Test parsing transaction webhook with bytes input.

        Args:
            sample_transaction_payload: Sample transaction payload fixture.
        """
        body_bytes = json.dumps(sample_transaction_payload).encode("utf-8")

        transaction = parse_transaction_webhook(body=body_bytes)

        assert transaction.id == "tx_123456789"
        assert transaction.amount == -1250


class TestWebhookTypes:
    """Test webhook type definitions."""

    def test_transaction_webhook_payload_validation(self) -> None:
        """Test TransactionWebhookPayload validation."""
        valid_data = {
            "type": "transaction.created",
            "data": {
                "id": "tx_123",
                "amount": -500,
                "created": "2023-01-01T12:00:00Z",
                "currency": "GBP",
                "description": "Test Transaction",
                "account_balance": 100000,
                "category": "general",
                "is_load": False,
                "settled": "2023-01-01T12:00:00Z",
                "metadata": {},
                "notes": None,
                "decline_reason": None,
            },
        }

        payload = TransactionWebhookPayload(
            type=cast("Literal['transaction.created']", valid_data["type"]),
            data=Transaction(**cast("dict[str, Any]", valid_data["data"])),
        )
        assert payload.type == "transaction.created"
        assert payload.data.id == "tx_123"

    def test_webhook_payload_generic(self) -> None:
        """Test generic WebhookPayload validation."""
        data = {
            "type": "balance.updated",
            "data": {"account_id": "acc_123", "balance": 50000},
        }

        payload = WebhookPayload(
            type=cast("str", data["type"]), data=cast("dict[str, Any]", data["data"])
        )
        assert payload.type == "balance.updated"
        assert payload.data["account_id"] == "acc_123"

    def test_transaction_webhook_payload_invalid_type(self) -> None:
        """Test TransactionWebhookPayload with invalid type."""
        invalid_data = {
            "type": "balance.updated",
            "data": {
                "id": "tx_123",
                "amount": -500,
                "created": "2023-01-01T12:00:00Z",
                "currency": "GBP",
                "description": "Test Transaction",
                "account_balance": 100000,
                "category": "general",
                "is_load": False,
                "settled": "2023-01-01T12:00:00Z",
                "metadata": {},
                "notes": None,
                "decline_reason": None,
            },
        }

        with pytest.raises(
            ValidationError, match="Input should be 'transaction.created'"
        ):
            TransactionWebhookPayload(
                type=cast("Literal['transaction.created']", invalid_data["type"]),
                data=Transaction(**cast("dict[str, Any]", invalid_data["data"])),
            )


class TestWebhookIntegration:
    """Integration tests for webhook processing."""

    def test_full_transaction_workflow(self) -> None:
        """Test complete transaction webhook processing workflow."""
        webhook_body = {
            "type": "transaction.created",
            "data": {
                "id": "tx_integration_test",
                "amount": -750,
                "created": "2023-06-15T14:30:00Z",
                "currency": "GBP",
                "description": "Local Coffee Shop",
                "account_balance": 89250,
                "category": "eating_out",
                "is_load": False,
                "settled": "2023-06-15T14:30:00Z",
                "metadata": {"location": "High Street"},
                "notes": "Morning coffee",
                "decline_reason": None,
            },
        }

        payload = parse_webhook_payload(body=json.dumps(webhook_body))
        assert isinstance(payload, TransactionWebhookPayload)

        transaction = parse_transaction_webhook(body=json.dumps(webhook_body))

        assert payload.data.id == transaction.id
        assert payload.data.amount == transaction.amount
        assert payload.data.description == transaction.description

        amount_pounds = (
            abs(transaction.amount) / 100 if transaction.amount is not None else 0
        )
        balance_pounds = (transaction.account_balance or 0) / 100

        assert amount_pounds == 7.5
        assert balance_pounds == 892.5
        assert transaction.category == "eating_out"
        assert "coffee" in transaction.description.lower()

    def test_multiple_event_types(self) -> None:
        """Test handling multiple webhook event types."""
        events = [
            {
                "type": "transaction.created",
                "data": {
                    "id": "tx_multi_test1",
                    "amount": -250,
                    "created": "2023-06-15T10:00:00Z",
                    "currency": "GBP",
                    "description": "Bus Fare",
                    "account_balance": 99750,
                    "category": "transport",
                    "is_load": False,
                    "settled": "2023-06-15T10:00:00Z",
                    "metadata": {},
                    "notes": None,
                    "decline_reason": None,
                },
            },
            {
                "type": "balance.updated",
                "data": {
                    "account_id": "acc_test123",
                    "balance": 99500,
                    "currency": "GBP",
                },
            },
        ]

        for event_data in events:
            payload = parse_webhook_payload(body=json.dumps(event_data))

            if isinstance(payload, TransactionWebhookPayload):
                assert payload.data.description == "Bus Fare"
            else:
                assert payload.type == "balance.updated"
                assert payload.data["balance"] == 99500
