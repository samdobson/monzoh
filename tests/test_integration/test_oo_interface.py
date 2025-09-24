"""Tests for object-oriented interface."""

from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import Mock
from uuid import uuid4

import pytest

from monzoh.core import BaseSyncClient
from monzoh.models import Account, Balance, Pot, Transaction


class TestAccountOOInterface:
    """Test Account object-oriented interface."""

    def test_account_without_client_raises_error(self) -> None:
        """Test that Account methods raise error when no client is set."""
        account = Account(
            id="acc_123",
            description="Test Account",
            created=datetime.now(tz=timezone.utc),
        )

        with pytest.raises(RuntimeError, match="No client available"):
            account.get_balance()

        with pytest.raises(RuntimeError, match="No client available"):
            account.list_transactions()

        with pytest.raises(RuntimeError, match="No client available"):
            account.list_pots()

        from monzoh.models.feed import FeedItemParams

        params = FeedItemParams(
            title="Test", image_url="https://example.com/image.jpg"
        )
        with pytest.raises(RuntimeError, match="No client available"):
            account.create_feed_item(params)

    def test_account_get_balance(self) -> None:
        """Test Account.get_balance() method."""
        mock_client = Mock(spec=BaseSyncClient)
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
        mock_client._get.return_value = mock_response

        account = Account(
            id="acc_123",
            description="Test Account",
            created=datetime.now(tz=timezone.utc),
        )
        account._set_client(mock_client)

        balance = account.get_balance()

        assert isinstance(balance, Balance)
        assert balance.balance == Decimal("50.00")
        assert balance.total_balance == Decimal("60.00")
        assert balance.currency == "GBP"
        assert balance.spend_today == Decimal("1.00")

        mock_client._get.assert_called_once_with(
            "/balance", params={"account_id": "acc_123"}
        )

    def test_account_list_transactions(self) -> None:
        """Test Account.list_transactions() method."""
        mock_client = Mock(spec=BaseSyncClient)
        mock_client._prepare_pagination_params.return_value = {"limit": 10}
        mock_client._prepare_expand_params.return_value = []
        mock_response = Mock()
        mock_response.json.return_value = {
            "transactions": [
                {
                    "id": "tx_123",
                    "amount": -1000,
                    "created": datetime.now(tz=timezone.utc).isoformat(),
                    "currency": "GBP",
                    "description": "Test Transaction",
                    "is_load": False,
                }
            ]
        }
        mock_client._get.return_value = mock_response

        account = Account(
            id="acc_123",
            description="Test Account",
            created=datetime.now(tz=timezone.utc),
        )
        account._set_client(mock_client)

        transactions = account.list_transactions(limit=10)

        assert len(transactions) == 1
        assert isinstance(transactions[0], Transaction)
        assert transactions[0].id == "tx_123"
        assert transactions[0].amount == -1000
        assert transactions[0]._client == mock_client

    def test_account_list_pots(self) -> None:
        """Test Account.list_pots() method."""
        mock_client = Mock(spec=BaseSyncClient)
        mock_response = Mock()
        mock_response.json.return_value = {
            "pots": [
                {
                    "id": "pot_123",
                    "name": "Savings",
                    "style": "beach_ball",
                    "balance": 10000,
                    "currency": "GBP",
                    "created": datetime.now(tz=timezone.utc).isoformat(),
                    "updated": datetime.now(tz=timezone.utc).isoformat(),
                    "deleted": False,
                }
            ]
        }
        mock_client._get.return_value = mock_response

        account = Account(
            id="acc_123",
            description="Test Account",
            created=datetime.now(tz=timezone.utc),
        )
        account._set_client(mock_client)

        pots = account.list_pots()

        assert len(pots) == 1
        assert isinstance(pots[0], Pot)
        assert pots[0].id == "pot_123"
        assert pots[0].name == "Savings"
        assert pots[0]._client == mock_client
        assert pots[0]._source_account_id == "acc_123"

    def test_account_create_feed_item(self) -> None:
        """Test Account.create_feed_item() method."""
        from monzoh.models.feed import FeedItemParams

        mock_client = Mock(spec=BaseSyncClient)
        mock_response = Mock()
        mock_response.json.return_value = {}
        mock_client._post.return_value = mock_response

        account = Account(
            id="acc_123",
            description="Test Account",
            created=datetime.now(tz=timezone.utc),
        )
        account._set_client(mock_client)

        params = FeedItemParams(
            title="Test Feed Item", image_url="https://example.com/image.jpg"
        )
        account.create_feed_item(params)

        mock_client._post.assert_called_once_with(
            "/feed",
            data={
                "account_id": "acc_123",
                "type": "basic",
                "params[title]": "Test Feed Item",
                "params[image_url]": "https://example.com/image.jpg",
            },
        )

    def test_account_create_feed_item_with_all_params(self) -> None:
        """Test Account.create_feed_item() method with all parameters."""
        from monzoh.models.feed import FeedItemParams

        mock_client = Mock(spec=BaseSyncClient)
        mock_response = Mock()
        mock_response.json.return_value = {}
        mock_client._post.return_value = mock_response

        account = Account(
            id="acc_123",
            description="Test Account",
            created=datetime.now(tz=timezone.utc),
        )
        account._set_client(mock_client)

        params = FeedItemParams(
            title="Test Feed Item",
            image_url="https://example.com/image.jpg",
            body="Test body text",
            url="https://example.com/redirect",
            background_color="#FF0000",
            title_color="#000000",
            body_color="#333333",
        )
        account.create_feed_item(params)

        mock_client._post.assert_called_once_with(
            "/feed",
            data={
                "account_id": "acc_123",
                "type": "basic",
                "url": "https://example.com/redirect",
                "params[title]": "Test Feed Item",
                "params[image_url]": "https://example.com/image.jpg",
                "params[body]": "Test body text",
                "params[background_color]": "#FF0000",
                "params[title_color]": "#000000",
                "params[body_color]": "#333333",
            },
        )


class TestPotOOInterface:
    """Test Pot object-oriented interface."""

    def test_pot_without_client_raises_error(self) -> None:
        """Test that Pot methods raise error when no client is set."""
        pot = Pot(
            id="pot_123",
            name="Savings",
            style="beach_ball",
            balance=10000,
            currency="GBP",
            created=datetime.now(tz=timezone.utc),
            updated=datetime.now(tz=timezone.utc),
        )

        with pytest.raises(RuntimeError, match="No client available"):
            pot.deposit(1000)

        with pytest.raises(RuntimeError, match="No client available"):
            pot.withdraw(500)

    def test_pot_deposit(self) -> None:
        """Test Pot.deposit() method."""
        mock_client = Mock(spec=BaseSyncClient)
        mock_response = Mock()
        updated_pot_data = {
            "id": "pot_123",
            "name": "Savings",
            "style": "beach_ball",
            "balance": 11000,
            "currency": "GBP",
            "created": datetime.now(tz=timezone.utc).isoformat(),
            "updated": datetime.now(tz=timezone.utc).isoformat(),
            "deleted": False,
        }
        mock_response.json.return_value = updated_pot_data
        mock_client._put.return_value = mock_response

        pot = Pot(
            id="pot_123",
            name="Savings",
            style="beach_ball",
            balance=10000,
            currency="GBP",
            created=datetime.now(tz=timezone.utc),
            updated=datetime.now(tz=timezone.utc),
        )
        pot._set_client(mock_client)
        pot._source_account_id = "acc_123"

        updated_pot = pot.deposit(10.00)

        assert isinstance(updated_pot, Pot)
        assert updated_pot.balance == Decimal("110.00")
        assert updated_pot._client == mock_client
        assert updated_pot._source_account_id == "acc_123"

        mock_client._put.assert_called_once()
        call_args = mock_client._put.call_args
        assert call_args[0][0] == "/pots/pot_123/deposit"
        assert call_args[1]["data"]["source_account_id"] == "acc_123"
        assert call_args[1]["data"]["amount"] == "1000"
        assert "dedupe_id" in call_args[1]["data"]

    def test_pot_deposit_with_custom_dedupe_id(self) -> None:
        """Test Pot.deposit() with custom dedupe_id."""
        mock_client = Mock(spec=BaseSyncClient)
        mock_response = Mock()
        mock_response.json.return_value = {
            "id": "pot_123",
            "name": "Savings",
            "style": "beach_ball",
            "balance": 11000,
            "currency": "GBP",
            "created": datetime.now(tz=timezone.utc).isoformat(),
            "updated": datetime.now(tz=timezone.utc).isoformat(),
            "deleted": False,
        }
        mock_client._put.return_value = mock_response

        pot = Pot(
            id="pot_123",
            name="Savings",
            style="beach_ball",
            balance=10000,
            currency="GBP",
            created=datetime.now(tz=timezone.utc),
            updated=datetime.now(tz=timezone.utc),
        )
        pot._set_client(mock_client)
        pot._source_account_id = "acc_123"

        custom_dedupe_id = str(uuid4())
        pot.deposit(10.00, dedupe_id=custom_dedupe_id)

        call_args = mock_client._put.call_args
        assert call_args[1]["data"]["dedupe_id"] == custom_dedupe_id

    def test_pot_withdraw(self) -> None:
        """Test Pot.withdraw() method."""
        mock_client = Mock(spec=BaseSyncClient)
        mock_response = Mock()
        updated_pot_data = {
            "id": "pot_123",
            "name": "Savings",
            "style": "beach_ball",
            "balance": 9500,
            "currency": "GBP",
            "created": datetime.now(tz=timezone.utc).isoformat(),
            "updated": datetime.now(tz=timezone.utc).isoformat(),
            "deleted": False,
        }
        mock_response.json.return_value = updated_pot_data
        mock_client._put.return_value = mock_response

        pot = Pot(
            id="pot_123",
            name="Savings",
            style="beach_ball",
            balance=10000,
            currency="GBP",
            created=datetime.now(tz=timezone.utc),
            updated=datetime.now(tz=timezone.utc),
        )
        pot._set_client(mock_client)
        pot._source_account_id = "acc_123"

        updated_pot = pot.withdraw(5.00)

        assert isinstance(updated_pot, Pot)
        assert updated_pot.balance == Decimal("95.00")
        assert updated_pot._client == mock_client
        assert updated_pot._source_account_id == "acc_123"

        mock_client._put.assert_called_once()
        call_args = mock_client._put.call_args
        assert call_args[0][0] == "/pots/pot_123/withdraw"
        assert call_args[1]["data"]["destination_account_id"] == "acc_123"
        assert call_args[1]["data"]["amount"] == "500"

    def test_pot_without_source_account_raises_error(self) -> None:
        """Test that pot methods raise error when no source account is available."""
        pot = Pot(
            id="pot_123",
            name="Savings",
            style="beach_ball",
            balance=10000,
            currency="GBP",
            created=datetime.now(tz=timezone.utc),
            updated=datetime.now(tz=timezone.utc),
        )
        mock_client = Mock(spec=BaseSyncClient)
        pot._set_client(mock_client)

        with pytest.raises(RuntimeError, match="No source account ID available"):
            pot.deposit(10.00)

        with pytest.raises(RuntimeError, match="No source account ID available"):
            pot.withdraw(5.00)


class TestTransactionOOInterface:
    """Test Transaction object-oriented interface."""

    def test_transaction_without_client_raises_error(self) -> None:
        """Test that Transaction methods raise error when no client is set."""
        transaction = Transaction(
            id="tx_123",
            amount=-1000,
            created=datetime.now(tz=timezone.utc),
            currency="GBP",
            description="Test Transaction",
        )

        with pytest.raises(RuntimeError, match="No client available"):
            transaction.annotate({"key": "value"})

        with pytest.raises(RuntimeError, match="No client available"):
            transaction.refresh()

    def test_transaction_annotate(self) -> None:
        """Test Transaction.annotate() method."""
        mock_client = Mock(spec=BaseSyncClient)
        mock_response = Mock()
        updated_transaction_data = {
            "id": "tx_123",
            "amount": -1000,
            "created": datetime.now(tz=timezone.utc).isoformat(),
            "currency": "GBP",
            "description": "Test Transaction",
            "metadata": {"key": "value"},
        }
        mock_response.json.return_value = {"transaction": updated_transaction_data}
        mock_client._patch.return_value = mock_response

        transaction = Transaction(
            id="tx_123",
            amount=-1000,
            created=datetime.now(tz=timezone.utc),
            currency="GBP",
            description="Test Transaction",
        )
        transaction._set_client(mock_client)

        updated_transaction = transaction.annotate({"key": "value"})

        assert isinstance(updated_transaction, Transaction)
        assert updated_transaction.metadata == {"key": "value"}
        assert updated_transaction._client == mock_client

        mock_client._patch.assert_called_once()
        call_args = mock_client._patch.call_args
        assert call_args[0][0] == "/transactions/tx_123"
        assert call_args[1]["data"] == {"metadata[key]": "value"}

    def test_transaction_refresh(self) -> None:
        """Test Transaction.refresh() method."""
        mock_client = Mock(spec=BaseSyncClient)
        mock_client._prepare_expand_params.return_value = [("expand[]", "merchant")]
        mock_response = Mock()
        refreshed_transaction_data = {
            "id": "tx_123",
            "amount": -1000,
            "created": datetime.now(tz=timezone.utc).isoformat(),
            "currency": "GBP",
            "description": "Updated Test Transaction",
        }
        mock_response.json.return_value = {"transaction": refreshed_transaction_data}
        mock_client._get.return_value = mock_response

        transaction = Transaction(
            id="tx_123",
            amount=-1000,
            created=datetime.now(tz=timezone.utc),
            currency="GBP",
            description="Test Transaction",
        )
        transaction._set_client(mock_client)

        refreshed_transaction = transaction.refresh(expand=["merchant"])

        assert isinstance(refreshed_transaction, Transaction)
        assert refreshed_transaction.description == "Updated Test Transaction"
        assert refreshed_transaction._client == mock_client

        mock_client._get.assert_called_once_with(
            "/transactions/tx_123", params=[("expand[]", "merchant")]
        )


class TestModelClientIntegration:
    """Test integration between models and client setting."""

    def test_set_client_returns_self(self) -> None:
        """Test that _set_client returns the model instance."""
        mock_client = Mock(spec=BaseSyncClient)

        account = Account(
            id="acc_123",
            description="Test Account",
            created=datetime.now(tz=timezone.utc),
        )
        result = account._set_client(mock_client)

        assert result is account
        assert account._client == mock_client

    def test_client_exclusion_from_serialization(self) -> None:
        """Test that _client field is excluded from serialization."""
        mock_client = Mock(spec=BaseSyncClient)

        account = Account(
            id="acc_123",
            description="Test Account",
            created=datetime.now(tz=timezone.utc),
        )
        account._set_client(mock_client)

        data = account.model_dump()
        assert "_client" not in data

        json_str = account.model_dump_json()
        assert "_client" not in json_str

    def test_client_exclusion_from_repr(self) -> None:
        """Test that _client field is excluded from repr."""
        mock_client = Mock(spec=BaseSyncClient)

        account = Account(
            id="acc_123",
            description="Test Account",
            created=datetime.now(tz=timezone.utc),
        )
        account._set_client(mock_client)

        repr_str = repr(account)
        assert "_client" not in repr_str
