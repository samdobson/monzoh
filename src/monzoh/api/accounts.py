"""Accounts API endpoints."""

from ..core import BaseSyncClient
from ..models import Account, AccountsResponse, Balance


class AccountsAPI:
    """Accounts API client.

    Args:
        client: Base API client
    """

    def __init__(self, client: BaseSyncClient) -> None:
        self.client = client

    def list(self, account_type: str | None = None) -> list[Account]:
        """List accounts owned by the current user.

        Args:
            account_type: Filter by account type ('uk_retail', 'uk_retail_joint')

        Returns:
            List of accounts with client attached
        """
        params = {}
        if account_type:
            params["account_type"] = account_type

        response = self.client._get("/accounts", params=params)
        accounts_response = AccountsResponse(**response.json())

        # Set client on all account objects
        for account in accounts_response.accounts:
            account._set_client(self.client)

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
