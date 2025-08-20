"""Accounts API endpoints."""

from typing import Optional

from .client import BaseSyncClient
from .models import Account, AccountsResponse, Balance


class AccountsAPI:
    """Accounts API client."""

    def __init__(self, client: BaseSyncClient) -> None:
        """Initialize accounts API.

        Args:
            client: Base API client
        """
        self.client = client

    def list(self, account_type: Optional[str] = None) -> list[Account]:
        """List accounts owned by the current user.

        Args:
            account_type: Filter by account type ('uk_retail', 'uk_retail_joint')

        Returns:
            List of accounts
        """
        params = {}
        if account_type:
            params["account_type"] = account_type

        response = self.client._get("/accounts", params=params)
        accounts_response = AccountsResponse(**response.json())
        return accounts_response.accounts

    def get_balance(self, account_id: str) -> Balance:
        """Get balance information for a specific account.

        Args:
            account_id: Account ID

        Returns:
            Account balance information
        """
        params = {"account_id": account_id}
        response = self.client._get("/balance", params=params)
        return Balance(**response.json())
