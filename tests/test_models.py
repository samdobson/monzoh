"""Tests for Pydantic models."""

from datetime import datetime
from decimal import Decimal
from typing import Any
from unittest.mock import Mock

import pytest

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
from monzoh.models.feed import FeedItemParams


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
            "balance_including_flexible_savings": False,
            "local_currency": "GBP",
            "local_exchange_rate": 100,
            "local_spend": 100,
        }
        balance = Balance(**data)

        assert balance.balance == Decimal("50.00")
        assert balance.total_balance == Decimal("60.00")
        assert balance.currency == "GBP"
        assert balance.spend_today == Decimal("1.00")

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
        assert pot.balance == Decimal("100.00")
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

    def test_feed_item_params_model_minimal(self) -> None:
        """Test FeedItemParams model with minimal required fields."""
        data: dict[str, Any] = {
            "title": "Test Feed Item",
            "image_url": "https://example.com/image.jpg",
        }
        params = FeedItemParams(**data)

        assert params.title == "Test Feed Item"
        assert params.image_url == "https://example.com/image.jpg"
        assert params.body is None
        assert params.url is None
        assert params.background_color is None
        assert params.title_color is None
        assert params.body_color is None

    def test_feed_item_params_model_full(self) -> None:
        """Test FeedItemParams model with all fields."""
        data: dict[str, Any] = {
            "title": "Test Feed Item",
            "image_url": "https://example.com/image.jpg",
            "body": "Test body text",
            "url": "https://example.com/redirect",
            "background_color": "#FF0000",
            "title_color": "#000000",
            "body_color": "#333333",
        }
        params = FeedItemParams(**data)

        assert params.title == "Test Feed Item"
        assert params.image_url == "https://example.com/image.jpg"
        assert params.body == "Test body text"
        assert params.url == "https://example.com/redirect"
        assert params.background_color == "#FF0000"
        assert params.title_color == "#000000"
        assert params.body_color == "#333333"

    def test_feed_item_params_model_dump_exclude_none(self) -> None:
        """Test FeedItemParams model_dump excludes None values."""
        data: dict[str, Any] = {
            "title": "Test Feed Item",
            "image_url": "https://example.com/image.jpg",
            "body": "Test body text",
        }
        params = FeedItemParams(**data)

        dumped = params.model_dump(exclude_none=True)

        assert "title" in dumped
        assert "image_url" in dumped
        assert "body" in dumped
        assert "url" not in dumped
        assert "background_color" not in dumped
        assert "title_color" not in dumped
        assert "body_color" not in dumped


class TestPotMethods:
    """Test Pot model methods."""

    def test_pot_ensure_client_no_client(self) -> None:
        """Test _ensure_client raises error when no client is set."""
        pot = Pot(
            id="pot_123",
            name="Savings",
            style="beach_ball",
            balance=10000,
            currency="GBP",
            created=datetime(2023, 1, 1, 12, 0, 0),
            updated=datetime(2023, 1, 1, 12, 0, 0),
            deleted=False,
        )

        with pytest.raises(RuntimeError, match="No client available"):
            pot._ensure_client()

    def test_pot_set_client(self) -> None:
        """Test _set_client method."""
        pot = Pot(
            id="pot_123",
            name="Savings",
            style="beach_ball",
            balance=10000,
            currency="GBP",
            created=datetime(2023, 1, 1, 12, 0, 0),
            updated=datetime(2023, 1, 1, 12, 0, 0),
            deleted=False,
        )

        mock_client = Mock()
        result = pot._set_client(mock_client)

        assert result is pot
        assert pot._client is mock_client

    def test_pot_get_source_account_id_from_source(self) -> None:
        """Test _get_source_account_id uses _source_account_id."""
        pot = Pot(
            id="pot_123",
            name="Savings",
            style="beach_ball",
            balance=10000,
            currency="GBP",
            created=datetime(2023, 1, 1, 12, 0, 0),
            updated=datetime(2023, 1, 1, 12, 0, 0),
            deleted=False,
        )
        pot._source_account_id = "acc_123"

        assert pot._get_source_account_id() == "acc_123"

    @pytest.mark.asyncio
    async def test_pot_async_withdraw_with_async_client(self) -> None:
        """Test awithdraw with async client."""
        from unittest.mock import patch

        from monzoh.core.async_base import BaseAsyncClient

        pot = Pot(
            id="pot_123",
            name="Savings",
            style="beach_ball",
            balance=15000,
            currency="GBP",
            created=datetime(2023, 1, 1, 12, 0, 0),
            updated=datetime(2023, 1, 1, 12, 0, 0),
            deleted=False,
        )

        mock_client = Mock(spec=BaseAsyncClient)
        mock_response = Mock()
        mock_response.json.return_value = {
            "id": "pot_123",
            "name": "Savings",
            "style": "beach_ball",
            "balance": 10000,
            "currency": "GBP",
            "created": "2023-01-01T12:00:00Z",
            "updated": "2023-01-01T12:00:00Z",
            "deleted": False,
        }
        mock_client._put.return_value = mock_response

        pot._set_client(mock_client)
        pot._source_account_id = "acc_123"

        with patch("monzoh.models.pots.uuid4") as mock_uuid:
            mock_uuid.return_value = Mock(__str__=Mock(return_value="test-uuid"))
            result = await pot.awithdraw(amount=Decimal("50.00"))

        mock_client._put.assert_called_once_with(
            "/pots/pot_123/withdraw",
            data={
                "destination_account_id": "acc_123",
                "amount": "5000",
                "dedupe_id": "test-uuid",
            },
        )
        assert isinstance(result, Pot)
        assert result.balance == Decimal("100.00")

    @pytest.mark.asyncio
    async def test_pot_async_withdraw_wrong_client_type(self) -> None:
        """Test awithdraw raises error with sync client."""
        from monzoh.core.base import BaseSyncClient

        pot = Pot(
            id="pot_123",
            name="Savings",
            style="beach_ball",
            balance=15000,
            currency="GBP",
            created=datetime(2023, 1, 1, 12, 0, 0),
            updated=datetime(2023, 1, 1, 12, 0, 0),
            deleted=False,
        )

        mock_client = Mock(spec=BaseSyncClient)
        pot._set_client(mock_client)

        with pytest.raises(
            RuntimeError, match="Async method called on pot with sync client"
        ):
            await pot.awithdraw(amount=Decimal("50.00"))

    def test_pot_convert_goal_amount_none(self) -> None:
        """Test convert_goal_amount_minor_to_major_units with None."""
        result = Pot.convert_goal_amount_minor_to_major_units(None)
        assert result is None

    def test_pot_convert_goal_amount_value(self) -> None:
        """Test convert_goal_amount_minor_to_major_units with value."""
        result = Pot.convert_goal_amount_minor_to_major_units(5000)
        assert result == Decimal("50.00")


class TestTransactionMethods:
    """Test Transaction model methods."""

    def test_transaction_upload_attachment_with_sync_client(self) -> None:
        """Test upload_attachment with sync client."""
        from unittest.mock import patch

        from monzoh.core.base import BaseSyncClient

        transaction = Transaction(
            id="tx_123",
            amount=-1000,
            created=datetime(2023, 1, 1, 12, 0, 0),
            currency="GBP",
            description="Test Transaction",
            is_load=False,
        )

        mock_client = Mock(spec=BaseSyncClient)
        transaction._set_client(mock_client)

        mock_attachment = Mock()

        with patch("monzoh.api.attachments.AttachmentsAPI") as mock_api_class:
            mock_api = Mock()
            mock_api.upload.return_value = mock_attachment
            mock_api_class.return_value = mock_api

            result = transaction.upload_attachment(
                file_path="/path/to/file.jpg",
                file_name="receipt.jpg",
                file_type="image/jpeg",
            )

        mock_api_class.assert_called_once_with(mock_client)
        mock_api.upload.assert_called_once_with(
            transaction_id="tx_123",
            file_path="/path/to/file.jpg",
            file_name="receipt.jpg",
            file_type="image/jpeg",
        )
        assert result is mock_attachment

    def test_transaction_upload_attachment_wrong_client_type(self) -> None:
        """Test upload_attachment raises error with async client."""
        from monzoh.core.async_base import BaseAsyncClient

        transaction = Transaction(
            id="tx_123",
            amount=-1000,
            created=datetime(2023, 1, 1, 12, 0, 0),
            currency="GBP",
            description="Test Transaction",
            is_load=False,
        )

        mock_client = Mock(spec=BaseAsyncClient)
        transaction._set_client(mock_client)

        with pytest.raises(
            RuntimeError, match="Sync method called on transaction with async client"
        ):
            transaction.upload_attachment(
                file_path="/path/to/file.jpg",
                file_name="receipt.jpg",
                file_type="image/jpeg",
            )
