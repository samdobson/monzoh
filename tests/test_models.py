"""Tests for Pydantic models."""

from datetime import datetime
from typing import Any

from monzoh.models import (
    Account,
    Balance,
    OAuthToken,
    Pot,
    Receipt,
    ReceiptItem,
    Transaction,
    WhoAmI,
)


class TestModels:
    """Test Pydantic models."""

    def test_account_model(self) -> None:
        """Test Account model."""
        data: dict[str, Any] = {
            "id": "acc_123",
            "description": "Test Account",
            "created": datetime(2023, 1, 1, 12, 0, 0),
        }
        account = Account(**data)

        assert account.id == "acc_123"
        assert account.description == "Test Account"
        assert isinstance(account.created, datetime)

    def test_balance_model(self) -> None:
        """Test Balance model."""
        data: dict[str, Any] = {
            "balance": 5000,
            "total_balance": 6000,
            "currency": "GBP",
            "spend_today": 100,
        }
        balance = Balance(**data)

        assert balance.balance == 5000
        assert balance.total_balance == 6000
        assert balance.currency == "GBP"
        assert balance.spend_today == 100

    def test_transaction_model(self) -> None:
        """Test Transaction model."""
        data: dict[str, Any] = {
            "id": "tx_123",
            "amount": -1000,
            "created": datetime(2023, 1, 1, 12, 0, 0),
            "currency": "GBP",
            "description": "Test Transaction",
            "is_load": False,
        }
        transaction = Transaction(**data)

        assert transaction.id == "tx_123"
        assert transaction.amount == -1000
        assert transaction.currency == "GBP"
        assert transaction.is_load is False

    def test_pot_model(self) -> None:
        """Test Pot model."""
        data: dict[str, Any] = {
            "id": "pot_123",
            "name": "Savings",
            "style": "beach_ball",
            "balance": 10000,
            "currency": "GBP",
            "created": datetime(2023, 1, 1, 12, 0, 0),
            "updated": datetime(2023, 1, 1, 12, 0, 0),
            "deleted": False,
        }
        pot = Pot(**data)

        assert pot.id == "pot_123"
        assert pot.name == "Savings"
        assert pot.balance == 10000
        assert pot.deleted is False

    def test_receipt_model(self) -> None:
        """Test Receipt model."""
        item_data: dict[str, Any] = {
            "description": "Coffee",
            "amount": 300,
            "currency": "GBP",
        }
        receipt_data: dict[str, Any] = {
            "external_id": "receipt_123",
            "transaction_id": "tx_123",
            "total": 300,
            "currency": "GBP",
            "items": [item_data],
        }

        receipt = Receipt(**receipt_data)

        assert receipt.external_id == "receipt_123"
        assert receipt.total == 300
        assert len(receipt.items) == 1
        assert isinstance(receipt.items[0], ReceiptItem)

    def test_oauth_token_model(self) -> None:
        """Test OAuth token model."""
        data: dict[str, Any] = {
            "access_token": "access_123",
            "client_id": "client_123",
            "expires_in": 3600,
            "token_type": "Bearer",
            "user_id": "user_123",
        }
        token = OAuthToken(**data)

        assert token.access_token == "access_123"
        assert token.expires_in == 3600
        assert token.token_type == "Bearer"

    def test_whoami_model(self) -> None:
        """Test WhoAmI model."""
        data: dict[str, Any] = {
            "authenticated": True,
            "client_id": "client_123",
            "user_id": "user_123",
        }
        whoami = WhoAmI(**data)

        assert whoami.authenticated is True
        assert whoami.client_id == "client_123"
        assert whoami.user_id == "user_123"
