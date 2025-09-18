"""Integration tests for AsyncMonzoClient with OO interface."""

from datetime import datetime
from decimal import Decimal
from unittest.mock import AsyncMock, Mock

import pytest

from monzoh.async_client import AsyncMonzoClient
from monzoh.core.async_base import BaseAsyncClient


class TestAsyncClientOOIntegration:
    """Test AsyncMonzoClient with object-oriented interface."""

    @pytest.mark.asyncio
    async def test_client_accounts_list_sets_client(self) -> None:
        """Test that client.accounts.list() returns accounts with client set."""
        mock_base_client = Mock(spec=BaseAsyncClient)
        mock_response = Mock()
        mock_response.json.return_value = {
            "accounts": [
                {
                    "id": "acc_123",
                    "description": "Test Account",
                    "created": datetime.now().isoformat(),
                    "closed": False,
                }
            ]
        }
        mock_base_client._get = AsyncMock(return_value=mock_response)

        client = AsyncMonzoClient(access_token="test_token")
        client._base_client = mock_base_client
        client.accounts.client = mock_base_client

        accounts = await client.accounts.list()

        assert len(accounts) == 1
        account = accounts[0]
        assert account.id == "acc_123"
        assert account._client == mock_base_client

        mock_balance_response = Mock()
        mock_balance_response.json.return_value = {
            "balance": 5000,
            "total_balance": 6000,
            "currency": "GBP",
            "spend_today": 100,
        }
        mock_base_client._get = AsyncMock(return_value=mock_balance_response)

        balance = await account.aget_balance()
        assert balance.balance == Decimal("50.00")

    @pytest.mark.asyncio
    async def test_client_pots_list_sets_client_and_account(self) -> None:
        """Test that client.pots.list() returns pots with client and account set."""
        mock_base_client = Mock(spec=BaseAsyncClient)
        mock_response = Mock()
        mock_response.json.return_value = {
            "pots": [
                {
                    "id": "pot_123",
                    "name": "Savings",
                    "style": "beach_ball",
                    "balance": 10000,
                    "currency": "GBP",
                    "created": datetime.now().isoformat(),
                    "updated": datetime.now().isoformat(),
                    "deleted": False,
                }
            ]
        }
        mock_base_client._get = AsyncMock(return_value=mock_response)

        client = AsyncMonzoClient(access_token="test_token")
        client._base_client = mock_base_client
        client.pots.client = mock_base_client

        pots = await client.pots.list("acc_123")

        assert len(pots) == 1
        pot = pots[0]
        assert pot.id == "pot_123"
        assert pot._client == mock_base_client
        assert pot._source_account_id == "acc_123"

        mock_deposit_response = Mock()
        mock_deposit_response.json.return_value = {
            "id": "pot_123",
            "name": "Savings",
            "style": "beach_ball",
            "balance": 11000,
            "currency": "GBP",
            "created": datetime.now().isoformat(),
            "updated": datetime.now().isoformat(),
            "deleted": False,
        }
        mock_base_client._put = AsyncMock(return_value=mock_deposit_response)

        updated_pot = await pot.adeposit(1000)
        assert updated_pot.balance == Decimal("110.00")

    @pytest.mark.asyncio
    async def test_client_transactions_list_sets_client(self) -> None:
        """Test that client.transactions.list() returns transactions with client set."""
        mock_base_client = Mock(spec=BaseAsyncClient)
        mock_base_client._prepare_pagination_params.return_value = {}
        mock_base_client._prepare_expand_params.return_value = []
        mock_response = Mock()
        mock_response.json.return_value = {
            "transactions": [
                {
                    "id": "tx_123",
                    "amount": -1000,
                    "created": datetime.now().isoformat(),
                    "currency": "GBP",
                    "description": "Test Transaction",
                    "is_load": False,
                }
            ]
        }
        mock_base_client._get = AsyncMock(return_value=mock_response)

        client = AsyncMonzoClient(access_token="test_token")
        client._base_client = mock_base_client
        client.transactions.client = mock_base_client

        transactions = await client.transactions.list("acc_123")

        assert len(transactions) == 1
        transaction = transactions[0]
        assert transaction.id == "tx_123"
        assert transaction._client == mock_base_client

        mock_annotate_response = Mock()
        mock_annotate_response.json.return_value = {
            "transaction": {
                "id": "tx_123",
                "amount": -1000,
                "created": datetime.now().isoformat(),
                "currency": "GBP",
                "description": "Test Transaction",
                "metadata": {"category": "food"},
            }
        }
        mock_base_client._patch = AsyncMock(return_value=mock_annotate_response)

        updated_transaction = await transaction.aannotate({"category": "food"})
        assert updated_transaction.metadata == {"category": "food"}

    @pytest.mark.asyncio
    async def test_account_alist_transactions_sets_client_on_transactions(self) -> None:
        """Test that alist_transactions() sets client on transactions."""
        mock_base_client = Mock(spec=BaseAsyncClient)
        mock_base_client._prepare_pagination_params.return_value = {}
        mock_base_client._prepare_expand_params.return_value = []

        mock_response = Mock()
        mock_response.json.return_value = {
            "transactions": [
                {
                    "id": "tx_123",
                    "amount": -1000,
                    "created": datetime.now().isoformat(),
                    "currency": "GBP",
                    "description": "Test Transaction",
                    "is_load": False,
                }
            ]
        }
        mock_base_client._get = AsyncMock(return_value=mock_response)

        from monzoh.models import Account

        account = Account(
            id="acc_123",
            description="Test Account",
            created=datetime.now(),
        )
        account._set_client(mock_base_client)

        transactions = await account.alist_transactions()

        assert len(transactions) == 1
        transaction = transactions[0]
        assert transaction.id == "tx_123"
        assert transaction._client == mock_base_client

    @pytest.mark.asyncio
    async def test_account_alist_pots_sets_client_on_pots(self) -> None:
        """Test that account.alist_pots() sets client and account on returned pots."""
        mock_base_client = Mock(spec=BaseAsyncClient)

        mock_response = Mock()
        mock_response.json.return_value = {
            "pots": [
                {
                    "id": "pot_123",
                    "name": "Savings",
                    "style": "beach_ball",
                    "balance": 10000,
                    "currency": "GBP",
                    "created": datetime.now().isoformat(),
                    "updated": datetime.now().isoformat(),
                    "deleted": False,
                }
            ]
        }
        mock_base_client._get = AsyncMock(return_value=mock_response)

        from monzoh.models import Account

        account = Account(
            id="acc_123",
            description="Test Account",
            created=datetime.now(),
        )
        account._set_client(mock_base_client)

        pots = await account.alist_pots()

        assert len(pots) == 1
        pot = pots[0]
        assert pot.id == "pot_123"
        assert pot._client == mock_base_client
        assert pot._source_account_id == "acc_123"
