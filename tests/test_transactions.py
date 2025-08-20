"""Tests for transactions API."""

from datetime import datetime
from typing import Any

from monzoh.models import Transaction


class TestTransactionsAPI:
    """Test TransactionsAPI."""

    def test_list_transactions(
        self,
        monzo_sync_client: Any,
        mock_sync_http_client: Any,
        mock_httpx_response: Any,
        sample_transaction: Any,
    ) -> None:
        """Test listing transactions."""
        mock_response = mock_httpx_response(
            json_data={"transactions": [sample_transaction]}
        )
        monzo_sync_client._base_client._get.return_value = mock_response

        transactions = monzo_sync_client.transactions.list("acc_123")

        assert len(transactions) == 1
        assert isinstance(transactions[0], Transaction)
        assert transactions[0].id == sample_transaction["id"]
        assert transactions[0].amount == sample_transaction["amount"]

        monzo_sync_client._base_client._get.assert_called_once()
        call_args = monzo_sync_client._base_client._get.call_args
        assert "/transactions" in call_args[0][0]
        assert call_args[1]["params"]["account_id"] == "acc_123"

    def test_list_transactions_with_expand(
        self,
        monzo_sync_client: Any,
        mock_sync_http_client: Any,
        mock_httpx_response: Any,
        sample_transaction: Any,
    ) -> None:
        """Test listing transactions with expand."""
        mock_response = mock_httpx_response(
            json_data={"transactions": [sample_transaction]}
        )
        monzo_sync_client._base_client._get.return_value = mock_response

        transactions = monzo_sync_client.transactions.list(
            account_id="acc_123", expand=["merchant"]
        )

        assert len(transactions) == 1

        monzo_sync_client._base_client._get.assert_called_once()
        call_args = monzo_sync_client._base_client._get.call_args
        assert call_args[1]["params"]["expand[]"] == "merchant"

    def test_list_transactions_with_pagination(
        self,
        monzo_sync_client: Any,
        mock_sync_http_client: Any,
        mock_httpx_response: Any,
        sample_transaction: Any,
    ) -> None:
        """Test listing transactions with pagination."""
        mock_response = mock_httpx_response(
            json_data={"transactions": [sample_transaction]}
        )
        monzo_sync_client._base_client._get.return_value = mock_response

        since_time = datetime(2023, 1, 1, 12, 0, 0)
        transactions = monzo_sync_client.transactions.list(
            account_id="acc_123", limit=50, since=since_time
        )

        assert len(transactions) == 1

        monzo_sync_client._base_client._get.assert_called_once()
        call_args = monzo_sync_client._base_client._get.call_args
        assert call_args[1]["params"]["limit"] == "50"
        assert str(since_time) in call_args[1]["params"]["since"]

    def test_retrieve_transaction(
        self,
        monzo_sync_client: Any,
        mock_sync_http_client: Any,
        mock_httpx_response: Any,
        sample_transaction: Any,
    ) -> None:
        """Test retrieving a single transaction."""
        mock_response = mock_httpx_response(
            json_data={"transaction": sample_transaction}
        )
        monzo_sync_client._base_client._get.return_value = mock_response

        transaction = monzo_sync_client.transactions.retrieve("tx_123")

        assert isinstance(transaction, Transaction)
        assert transaction.id == sample_transaction["id"]

        monzo_sync_client._base_client._get.assert_called_once()
        call_args = monzo_sync_client._base_client._get.call_args
        assert "/transactions/tx_123" in call_args[0][0]

    def test_annotate_transaction(
        self,
        monzo_sync_client: Any,
        mock_sync_http_client: Any,
        mock_httpx_response: Any,
        sample_transaction: Any,
    ) -> None:
        """Test annotating a transaction."""
        updated_transaction = sample_transaction.copy()
        updated_transaction["metadata"] = {"foo": "bar"}

        mock_response = mock_httpx_response(
            json_data={"transaction": updated_transaction}
        )
        monzo_sync_client._base_client._patch.return_value = mock_response

        transaction = monzo_sync_client.transactions.annotate(
            "tx_123", {"foo": "bar", "delete_me": ""}
        )

        assert isinstance(transaction, Transaction)
        assert transaction.metadata["foo"] == "bar"

        monzo_sync_client._base_client._patch.assert_called_once()
        call_args = monzo_sync_client._base_client._patch.call_args
        assert "/transactions/tx_123" in call_args[0][0]
        assert call_args[1]["data"]["metadata[foo]"] == "bar"
        assert call_args[1]["data"]["metadata[delete_me]"] == ""
