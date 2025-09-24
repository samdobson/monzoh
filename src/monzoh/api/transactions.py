"""Transactions API endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import builtins
    from datetime import datetime

    from monzoh.core import BaseSyncClient
from monzoh.models import Transaction, TransactionResponse, TransactionsResponse


class TransactionsAPI:
    """Transactions API client.

    Args:
        client: Base API client
    """

    def __init__(self, client: BaseSyncClient) -> None:
        self.client = client

    def list(
        self,
        account_id: str,
        expand: builtins.list[str] | None = None,
        limit: int | None = None,
        since: datetime | str | None = None,
        before: datetime | None = None,
    ) -> builtins.list[Transaction]:
        """List transactions for an account.

        Args:
            account_id: Account ID
            expand: Fields to expand (e.g., ['merchant'])
            limit: Maximum number of results (1-100)
            since: Start time as RFC3339 timestamp or transaction ID
            before: End time as RFC3339 timestamp

        Returns:
            List of transactions
        """
        params = {"account_id": account_id}

        pagination_params = self.client._prepare_pagination_params(
            limit=limit, since=since, before=before
        )
        params.update(pagination_params)

        expand_params = self.client._prepare_expand_params(expand)
        if expand_params:
            params_list = list(params.items()) + expand_params
            response = self.client._get("/transactions", params=params_list)
        else:
            response = self.client._get("/transactions", params=params)
        transactions_response = TransactionsResponse(**response.json())

        for transaction in transactions_response.transactions:
            transaction._set_client(self.client)

        return transactions_response.transactions

    def retrieve(
        self, transaction_id: str, expand: builtins.list[str] | None = None
    ) -> Transaction:
        """Retrieve a single transaction by ID.

        Args:
            transaction_id: Transaction ID
            expand: Fields to expand (e.g., ['merchant'])

        Returns:
            Transaction details
        """
        expand_params = self.client._prepare_expand_params(expand)

        response = self.client._get(
            f"/transactions/{transaction_id}", params=expand_params
        )
        transaction_response = TransactionResponse(**response.json())
        transaction_response.transaction._set_client(self.client)
        return transaction_response.transaction

    def annotate(self, transaction_id: str, metadata: dict[str, Any]) -> Transaction:
        """Add annotations to a transaction.

        Args:
            transaction_id: Transaction ID
            metadata: Key-value metadata to store

        Returns:
            Updated transaction
        """
        data = {}
        for key, value in metadata.items():
            if value == "":
                data[f"metadata[{key}]"] = ""
            else:
                data[f"metadata[{key}]"] = str(value)

        response = self.client._patch(f"/transactions/{transaction_id}", data=data)
        transaction_response = TransactionResponse(**response.json())
        transaction_response.transaction._set_client(self.client)
        return transaction_response.transaction
