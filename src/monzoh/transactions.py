"""Transactions API endpoints."""

import builtins
from datetime import datetime
from typing import Any, Optional, Union

from .client import BaseSyncClient
from .models import Transaction, TransactionResponse, TransactionsResponse


class TransactionsAPI:
    """Transactions API client."""

    def __init__(self, client: BaseSyncClient) -> None:
        """Initialize transactions API.

        Args:
            client: Base API client
        """
        self.client = client

    def list(
        self,
        account_id: str,
        expand: Optional[list[str]] = None,
        limit: Optional[int] = None,
        since: Optional[Union[datetime, str]] = None,
        before: Optional[datetime] = None,
    ) -> list[Transaction]:
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

        # Add expand parameters
        if expand:
            for field in expand:
                params["expand[]"] = field

        # Add pagination parameters
        pagination_params = self.client._prepare_pagination_params(
            limit=limit, since=since, before=before
        )
        params.update(pagination_params)

        response = self.client._get("/transactions", params=params)
        transactions_response = TransactionsResponse(**response.json())
        return transactions_response.transactions

    def retrieve(
        self, transaction_id: str, expand: Optional[builtins.list[str]] = None
    ) -> Transaction:
        """Retrieve a single transaction by ID.

        Args:
            transaction_id: Transaction ID
            expand: Fields to expand (e.g., ['merchant'])

        Returns:
            Transaction details
        """
        params = {}
        if expand:
            for field in expand:
                params["expand[]"] = field

        response = self.client._get(
            f"/transactions/{transaction_id}", params=params if params else None
        )
        transaction_response = TransactionResponse(**response.json())
        return transaction_response.transaction

    def annotate(self, transaction_id: str, metadata: dict[str, Any]) -> Transaction:
        """Add annotations to a transaction.

        Args:
            transaction_id: Transaction ID
            metadata: Key-value metadata to store

        Returns:
            Updated transaction
        """
        # Prepare form data for metadata
        data = {}
        for key, value in metadata.items():
            # Handle the special case of deleting metadata
            if value == "":
                data[f"metadata[{key}]"] = ""
            else:
                data[f"metadata[{key}]"] = str(value)

        response = self.client._patch(f"/transactions/{transaction_id}", data=data)
        transaction_response = TransactionResponse(**response.json())
        return transaction_response.transaction
