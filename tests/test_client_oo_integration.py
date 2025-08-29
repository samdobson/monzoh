"""Integration tests for MonzoClient with OO interface."""

from datetime import datetime
from unittest.mock import Mock

from monzoh.client import MonzoClient
from monzoh.core import BaseSyncClient


class TestClientOOIntegration:
    """Test MonzoClient with object-oriented interface."""

    def test_client_accounts_list_sets_client(self) -> None:
        """Test that client.accounts.list() returns accounts with client set."""
        # Mock the base client
        mock_base_client = Mock(spec=BaseSyncClient)
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
        mock_base_client._get.return_value = mock_response

        # Create client and replace base client
        client = MonzoClient(access_token="test_token")
        client._base_client = mock_base_client
        client.accounts.client = mock_base_client

        # Test accounts.list()
        accounts = client.accounts.list()

        assert len(accounts) == 1
        account = accounts[0]
        assert account.id == "acc_123"
        # Verify client is set
        assert account._client == mock_base_client

        # Test that account methods work
        mock_balance_response = Mock()
        mock_balance_response.json.return_value = {
            "balance": 5000,
            "total_balance": 6000,
            "currency": "GBP",
            "spend_today": 100,
        }
        mock_base_client._get.return_value = mock_balance_response

        balance = account.get_balance()
        assert balance.balance == 5000

    def test_client_pots_list_sets_client_and_account(self) -> None:
        """Test that client.pots.list() returns pots with client and account set."""
        # Mock the base client
        mock_base_client = Mock(spec=BaseSyncClient)
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
        mock_base_client._get.return_value = mock_response

        # Create client and replace base client
        client = MonzoClient(access_token="test_token")
        client._base_client = mock_base_client
        client.pots.client = mock_base_client

        # Test pots.list()
        pots = client.pots.list("acc_123")

        assert len(pots) == 1
        pot = pots[0]
        assert pot.id == "pot_123"
        # Verify client and source account are set
        assert pot._client == mock_base_client
        assert pot._source_account_id == "acc_123"

        # Test that pot methods work
        mock_deposit_response = Mock()
        mock_deposit_response.json.return_value = {
            "id": "pot_123",
            "name": "Savings",
            "style": "beach_ball",
            "balance": 11000,  # Updated balance
            "currency": "GBP",
            "created": datetime.now().isoformat(),
            "updated": datetime.now().isoformat(),
            "deleted": False,
        }
        mock_base_client._put.return_value = mock_deposit_response

        updated_pot = pot.deposit(1000)
        assert updated_pot.balance == 11000

    def test_client_transactions_list_sets_client(self) -> None:
        """Test that client.transactions.list() returns transactions with client set."""
        # Mock the base client
        mock_base_client = Mock(spec=BaseSyncClient)
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
        mock_base_client._get.return_value = mock_response

        # Create client and replace base client
        client = MonzoClient(access_token="test_token")
        client._base_client = mock_base_client
        client.transactions.client = mock_base_client

        # Test transactions.list()
        transactions = client.transactions.list("acc_123")

        assert len(transactions) == 1
        transaction = transactions[0]
        assert transaction.id == "tx_123"
        # Verify client is set
        assert transaction._client == mock_base_client

        # Test that transaction methods work
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
        mock_base_client._patch.return_value = mock_annotate_response

        updated_transaction = transaction.annotate({"category": "food"})
        assert updated_transaction.metadata == {"category": "food"}

    def test_account_list_transactions_sets_client_on_transactions(self) -> None:
        """
        Test that account.list_transactions() sets client on returned transactions.
        """
        # Mock the base client
        mock_base_client = Mock(spec=BaseSyncClient)
        mock_base_client._prepare_pagination_params.return_value = {}
        mock_base_client._prepare_expand_params.return_value = []

        # Mock response for account.list_transactions()
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
        mock_base_client._get.return_value = mock_response

        # Create account with client set
        from monzoh.models import Account

        account = Account(
            id="acc_123",
            description="Test Account",
            created=datetime.now(),
        )
        account._set_client(mock_base_client)

        # Test account.list_transactions()
        transactions = account.list_transactions()

        assert len(transactions) == 1
        transaction = transactions[0]
        assert transaction.id == "tx_123"
        # Verify client is set on the transaction
        assert transaction._client == mock_base_client

    def test_account_list_pots_sets_client_on_pots(self) -> None:
        """Test that account.list_pots() sets client and account on returned pots."""
        # Mock the base client
        mock_base_client = Mock(spec=BaseSyncClient)

        # Mock response for account.list_pots()
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
        mock_base_client._get.return_value = mock_response

        # Create account with client set
        from monzoh.models import Account

        account = Account(
            id="acc_123",
            description="Test Account",
            created=datetime.now(),
        )
        account._set_client(mock_base_client)

        # Test account.list_pots()
        pots = account.list_pots()

        assert len(pots) == 1
        pot = pots[0]
        assert pot.id == "pot_123"
        # Verify client and source account are set on the pot
        assert pot._client == mock_base_client
        assert pot._source_account_id == "acc_123"
