"""Tests for transactions API."""

from datetime import datetime
from typing import Any

from monzoh.models import Transaction


class TestTransactionsAPI:
    """Test TransactionsAPI."""

    def test_list_transactions(
        self,
        monzo_client: Any,
        mock_http_client: Any,
        mock_response: Any,
        sample_transaction: Any,
    ) -> None:
        """Test listing transactions.

        Args:
            monzo_client: Monzo client fixture.
            mock_http_client: Mock HTTP client fixture.
            mock_response: Mock response fixture.
            sample_transaction: Sample transaction data fixture.
        """
        mock_response = mock_response(json_data={"transactions": [sample_transaction]})
        monzo_client._base_client._get.return_value = mock_response

        transactions = monzo_client.transactions.list("acc_123")

        assert len(transactions) == 1
        assert isinstance(transactions[0], Transaction)
        assert transactions[0].id == sample_transaction["id"]
        assert transactions[0].amount == sample_transaction["amount"]

        monzo_client._base_client._get.assert_called_once()
        call_args = monzo_client._base_client._get.call_args
        assert "/transactions" in call_args[0][0]
        assert call_args.kwargs["params"]["account_id"] == "acc_123"

    def test_list_transactions_with_expand(
        self,
        monzo_client: Any,
        mock_http_client: Any,
        mock_response: Any,
        sample_transaction: Any,
    ) -> None:
        """Test listing transactions with expand.

        Args:
            monzo_client: Monzo client fixture.
            mock_http_client: Mock HTTP client fixture.
            mock_response: Mock response fixture.
            sample_transaction: Sample transaction data fixture.
        """
        mock_response = mock_response(json_data={"transactions": [sample_transaction]})
        monzo_client._base_client._get.return_value = mock_response

        transactions = monzo_client.transactions.list(
            account_id="acc_123", expand=["merchant"]
        )

        assert len(transactions) == 1

        monzo_client._base_client._get.assert_called_once()
        call_args = monzo_client._base_client._get.call_args
        params = call_args[1]["params"]
        if isinstance(params, list):
            assert ("expand[]", "merchant") in params
        else:
            assert params["expand[]"] == "merchant"

    def test_list_transactions_with_pagination(
        self,
        monzo_client: Any,
        mock_http_client: Any,
        mock_response: Any,
        sample_transaction: Any,
    ) -> None:
        """Test listing transactions with pagination.

        Args:
            monzo_client: Monzo client fixture.
            mock_http_client: Mock HTTP client fixture.
            mock_response: Mock response fixture.
            sample_transaction: Sample transaction data fixture.
        """
        mock_response = mock_response(json_data={"transactions": [sample_transaction]})
        monzo_client._base_client._get.return_value = mock_response

        since_time = datetime(2023, 1, 1, 12, 0, 0)
        transactions = monzo_client.transactions.list(
            account_id="acc_123", limit=50, since=since_time
        )

        assert len(transactions) == 1

        monzo_client._base_client._get.assert_called_once()
        call_args = monzo_client._base_client._get.call_args
        params = call_args[1]["params"]
        assert isinstance(params, dict)
        assert params["limit"] == "50"
        assert str(since_time) in params["since"]

    def test_retrieve_transaction(
        self,
        monzo_client: Any,
        mock_http_client: Any,
        mock_response: Any,
        sample_transaction: Any,
    ) -> None:
        """Test retrieving a single transaction.

        Args:
            monzo_client: Monzo client fixture.
            mock_http_client: Mock HTTP client fixture.
            mock_response: Mock response fixture.
            sample_transaction: Sample transaction data fixture.
        """
        mock_response = mock_response(json_data={"transaction": sample_transaction})
        monzo_client._base_client._get.return_value = mock_response

        transaction = monzo_client.transactions.retrieve("tx_123")

        assert isinstance(transaction, Transaction)
        assert transaction.id == sample_transaction["id"]

        monzo_client._base_client._get.assert_called_once()
        call_args = monzo_client._base_client._get.call_args
        assert "/transactions/tx_123" in call_args[0][0]

    def test_annotate_transaction(
        self,
        monzo_client: Any,
        mock_http_client: Any,
        mock_response: Any,
        sample_transaction: Any,
    ) -> None:
        """Test annotating a transaction.

        Args:
            monzo_client: Monzo client fixture.
            mock_http_client: Mock HTTP client fixture.
            mock_response: Mock response fixture.
            sample_transaction: Sample transaction data fixture.
        """
        updated_transaction = sample_transaction.copy()
        updated_transaction["metadata"] = {"foo": "bar"}

        mock_response = mock_response(json_data={"transaction": updated_transaction})
        monzo_client._base_client._patch.return_value = mock_response

        transaction = monzo_client.transactions.annotate(
            "tx_123", {"foo": "bar", "delete_me": ""}
        )

        assert isinstance(transaction, Transaction)
        assert transaction.metadata["foo"] == "bar"

        monzo_client._base_client._patch.assert_called_once()
        call_args = monzo_client._base_client._patch.call_args
        assert "/transactions/tx_123" in call_args[0][0]
        assert call_args[1]["data"]["metadata[foo]"] == "bar"
        assert call_args[1]["data"]["metadata[delete_me]"] == ""
