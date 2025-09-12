"""Tests for async object-oriented interface."""

from datetime import datetime
from decimal import Decimal
from unittest.mock import AsyncMock, Mock

import pytest

from monzoh.core.async_base import BaseAsyncClient
from monzoh.models import Account, Balance, Pot, Transaction


class TestAsyncAccountOOInterface:
    """Test Account async object-oriented interface."""

    @pytest.mark.asyncio
    async def test_account_without_client_raises_error(self) -> None:
        """Test that Account async methods raise error when no client is set."""
        account = Account(
            id="acc_123",
            description="Test Account",
            created=datetime.now(),
        )

        with pytest.raises(RuntimeError, match="No client available"):
            await account.aget_balance()

        with pytest.raises(RuntimeError, match="No client available"):
            await account.alist_transactions()

        with pytest.raises(RuntimeError, match="No client available"):
            await account.alist_pots()

        with pytest.raises(RuntimeError, match="No client available"):
            from monzoh.models.feed import FeedItemParams

            params = FeedItemParams(
                title="Test", image_url="https://example.com/image.jpg"
            )
            await account.acreate_feed_item(params)

    @pytest.mark.asyncio
    async def test_account_aget_balance(self) -> None:
        """Test Account.aget_balance() method."""
        # Mock async client
        mock_client = Mock(spec=BaseAsyncClient)
        mock_response = Mock()
        mock_response.json.return_value = {
            "balance": 5000,
            "total_balance": 6000,
            "currency": "GBP",
            "spend_today": 100,
            "balance_including_flexible_savings": False,
            "local_currency": "GBP",
            "local_exchange_rate": 100,
            "local_spend": 100,
        }
        mock_client._get = AsyncMock(return_value=mock_response)

        # Create account and set client
        account = Account(
            id="acc_123",
            description="Test Account",
            created=datetime.now(),
        )
        account._set_client(mock_client)

        # Test aget_balance
        balance = await account.aget_balance()

        assert isinstance(balance, Balance)
        assert balance.balance == Decimal("50.00")
        assert balance.total_balance == Decimal("60.00")
        assert balance.currency == "GBP"
        assert balance.spend_today == Decimal("1.00")

        # Verify API call
        mock_client._get.assert_called_once_with(
            "/balance", params={"account_id": "acc_123"}
        )

    @pytest.mark.asyncio
    async def test_account_with_sync_client_raises_error(self) -> None:
        """Test that async methods raise error when sync client is set."""
        from monzoh.core import BaseSyncClient

        # Mock sync client
        mock_sync_client = Mock(spec=BaseSyncClient)

        # Create account and set sync client
        account = Account(
            id="acc_123",
            description="Test Account",
            created=datetime.now(),
        )
        account._set_client(mock_sync_client)

        # Test that async methods raise error
        with pytest.raises(
            RuntimeError, match="Async method called on account with sync client"
        ):
            await account.aget_balance()

    @pytest.mark.asyncio
    async def test_account_acreate_feed_item(self) -> None:
        """Test Account.acreate_feed_item() method."""
        from monzoh.models.feed import FeedItemParams

        # Mock async client
        mock_client = Mock(spec=BaseAsyncClient)
        mock_response = Mock()
        mock_response.json.return_value = {}
        mock_client._post = AsyncMock(return_value=mock_response)

        # Create account and set client
        account = Account(
            id="acc_123",
            description="Test Account",
            created=datetime.now(),
        )
        account._set_client(mock_client)

        # Test acreate_feed_item
        params = FeedItemParams(
            title="Test Feed Item",
            image_url="https://example.com/image.jpg",
            body="Test body text",
            url="https://example.com/redirect",
        )
        await account.acreate_feed_item(params)

        # Verify API call
        mock_client._post.assert_called_once_with(
            "/feed",
            data={
                "account_id": "acc_123",
                "type": "basic",
                "url": "https://example.com/redirect",
                "params[title]": "Test Feed Item",
                "params[image_url]": "https://example.com/image.jpg",
                "params[body]": "Test body text",
            },
        )

    @pytest.mark.asyncio
    async def test_account_acreate_feed_item_with_sync_client_raises_error(
        self,
    ) -> None:
        """Test that acreate_feed_item raises error when sync client is set."""
        from monzoh.core import BaseSyncClient
        from monzoh.models.feed import FeedItemParams

        # Mock sync client
        mock_sync_client = Mock(spec=BaseSyncClient)

        # Create account and set sync client
        account = Account(
            id="acc_123",
            description="Test Account",
            created=datetime.now(),
        )
        account._set_client(mock_sync_client)

        # Test that async method raises error
        params = FeedItemParams(title="Test", image_url="https://example.com/image.jpg")
        with pytest.raises(
            RuntimeError, match="Async method called on account with sync client"
        ):
            await account.acreate_feed_item(params)


class TestAsyncPotOOInterface:
    """Test Pot async object-oriented interface."""

    @pytest.mark.asyncio
    async def test_pot_adeposit(self) -> None:
        """Test Pot.adeposit() method."""
        # Mock async client
        mock_client = Mock(spec=BaseAsyncClient)
        mock_response = Mock()
        mock_response.json.return_value = {
            "id": "pot_123",
            "name": "Savings",
            "style": "beach_ball",
            "balance": 11000,  # Updated balance
            "currency": "GBP",
            "created": datetime.now().isoformat(),
            "updated": datetime.now().isoformat(),
            "deleted": False,
        }
        mock_client._put = AsyncMock(return_value=mock_response)

        # Create pot and set client
        pot = Pot(
            id="pot_123",
            name="Savings",
            style="beach_ball",
            balance=10000,
            currency="GBP",
            created=datetime.now(),
            updated=datetime.now(),
            deleted=False,
        )
        pot._set_client(mock_client)
        pot._source_account_id = "acc_123"

        # Test adeposit
        updated_pot = await pot.adeposit(10.00)  # £10.00 in major units

        assert isinstance(updated_pot, Pot)
        assert updated_pot.balance == Decimal("110.00")
        assert updated_pot._client == mock_client
        assert updated_pot._source_account_id == "acc_123"

        # Verify API call
        mock_client._put.assert_called_once()
        call_args = mock_client._put.call_args
        assert call_args[0][0] == "/pots/pot_123/deposit"
        assert call_args[1]["data"]["amount"] == "1000"
        assert call_args[1]["data"]["source_account_id"] == "acc_123"

    @pytest.mark.asyncio
    async def test_pot_with_sync_client_raises_error(self) -> None:
        """Test that async methods raise error when sync client is set."""
        from monzoh.core import BaseSyncClient

        # Mock sync client
        mock_sync_client = Mock(spec=BaseSyncClient)

        # Create pot and set sync client
        pot = Pot(
            id="pot_123",
            name="Savings",
            style="beach_ball",
            balance=10000,
            currency="GBP",
            created=datetime.now(),
            updated=datetime.now(),
            deleted=False,
        )
        pot._set_client(mock_sync_client)
        pot._source_account_id = "acc_123"

        # Test that async methods raise error
        with pytest.raises(
            RuntimeError, match="Async method called on pot with sync client"
        ):
            await pot.adeposit(10.00)


class TestAsyncTransactionOOInterface:
    """Test Transaction async object-oriented interface."""

    @pytest.mark.asyncio
    async def test_transaction_aannotate(self) -> None:
        """Test Transaction.aannotate() method."""
        # Mock async client
        mock_client = Mock(spec=BaseAsyncClient)
        mock_response = Mock()
        mock_response.json.return_value = {
            "transaction": {
                "id": "tx_123",
                "amount": -1000,
                "created": datetime.now().isoformat(),
                "currency": "GBP",
                "description": "Test Transaction",
                "metadata": {"category": "food"},
            }
        }
        mock_client._patch = AsyncMock(return_value=mock_response)

        # Create transaction and set client
        transaction = Transaction(
            id="tx_123",
            amount=-1000,
            created=datetime.now(),
            currency="GBP",
            description="Test Transaction",
        )
        transaction._set_client(mock_client)

        # Test aannotate
        updated_transaction = await transaction.aannotate({"category": "food"})

        assert isinstance(updated_transaction, Transaction)
        assert updated_transaction.metadata == {"category": "food"}
        assert updated_transaction._client == mock_client

        # Verify API call
        mock_client._patch.assert_called_once()
        call_args = mock_client._patch.call_args
        assert call_args[0][0] == "/transactions/tx_123"
        assert call_args[1]["data"]["metadata[category]"] == "food"

    @pytest.mark.asyncio
    async def test_transaction_with_sync_client_raises_error(self) -> None:
        """Test that async methods raise error when sync client is set."""
        from monzoh.core import BaseSyncClient

        # Mock sync client
        mock_sync_client = Mock(spec=BaseSyncClient)

        # Create transaction and set sync client
        transaction = Transaction(
            id="tx_123",
            amount=-1000,
            created=datetime.now(),
            currency="GBP",
            description="Test Transaction",
        )
        transaction._set_client(mock_sync_client)

        # Test that async methods raise error
        with pytest.raises(
            RuntimeError, match="Async method called on transaction with sync client"
        ):
            await transaction.aannotate({"category": "food"})
