"""Async accounts API endpoints."""

from ..core.async_base import BaseAsyncClient
from ..models import Account, AccountsResponse, Balance


class AsyncAccountsAPI:
    """Async accounts API client.

    Args:
        client: Base async API client
    """

    def __init__(self, client: BaseAsyncClient) -> None:
        self.client = client

    async def list(self, account_type: str | None = None) -> list[Account]:
        """List accounts owned by the current user.

        Args:
            account_type: Filter by account type ('uk_retail', 'uk_retail_joint')

        Returns:
            List of accounts
        """
        params = {}
        if account_type:
            params["account_type"] = account_type

        response = await self.client._get("/accounts", params=params)
        accounts_response = AccountsResponse(**response.json())

        for account in accounts_response.accounts:
            account._set_client(self.client)

        return accounts_response.accounts

    async def get_balance(self, account_id: str) -> Balance:
        """Get balance information for a specific account.

        Args:
            account_id: Account ID

        Returns:
            Account balance information
        """
        params = {"account_id": account_id}
        response = await self.client._get("/balance", params=params)
        return Balance(**response.json())
