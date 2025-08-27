"""Async pots API endpoints."""

from ..core.async_base import BaseAsyncClient
from ..models import Pot, PotsResponse


class AsyncPotsAPI:
    """Async pots API client."""

    def __init__(self, client: BaseAsyncClient) -> None:
        """Initialize async pots API.

        Args:
            client: Base async API client
        """
        self.client = client

    async def list(self, current_account_id: str) -> list[Pot]:
        """List pots for an account.

        Args:
            current_account_id: Account ID

        Returns:
            List of pots
        """
        params = {"current_account_id": current_account_id}

        response = await self.client._get("/pots", params=params)
        pots_response = PotsResponse(**response.json())
        return pots_response.pots

    async def deposit(
        self, pot_id: str, source_account_id: str, amount: int, dedupe_id: str
    ) -> Pot:
        """Deposit money into a pot.

        Args:
            pot_id: Pot ID
            source_account_id: Source account ID
            amount: Amount in minor units (e.g., pennies)
            dedupe_id: Unique ID to prevent duplicate deposits

        Returns:
            Updated pot
        """
        data = {
            "source_account_id": source_account_id,
            "amount": str(amount),
            "dedupe_id": dedupe_id,
        }

        response = await self.client._put(f"/pots/{pot_id}/deposit", data=data)
        return Pot(**response.json())

    async def withdraw(
        self, pot_id: str, destination_account_id: str, amount: int, dedupe_id: str
    ) -> Pot:
        """Withdraw money from a pot.

        Args:
            pot_id: Pot ID
            destination_account_id: Destination account ID
            amount: Amount in minor units (e.g., pennies)
            dedupe_id: Unique ID to prevent duplicate withdrawals

        Returns:
            Updated pot
        """
        data = {
            "destination_account_id": destination_account_id,
            "amount": str(amount),
            "dedupe_id": dedupe_id,
        }

        response = await self.client._put(f"/pots/{pot_id}/withdraw", data=data)
        return Pot(**response.json())
