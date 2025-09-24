"""Async pots API endpoints."""

from decimal import Decimal

from monzoh.core.async_base import BaseAsyncClient
from monzoh.models import Pot, PotsResponse
from monzoh.models.base import convert_amount_to_minor_units


class AsyncPotsAPI:
    """Async pots API client.

    Args:
        client: Base async API client
    """

    def __init__(self, client: BaseAsyncClient) -> None:
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

        for pot in pots_response.pots:
            pot._set_client(self.client)
            pot._source_account_id = current_account_id

        return pots_response.pots

    async def deposit(
        self,
        pot_id: str,
        source_account_id: str,
        amount: float | Decimal | str,
        dedupe_id: str,
    ) -> Pot:
        """Deposit money into a pot.

        Args:
            pot_id: Pot ID
            source_account_id: Source account ID
            amount: Amount in major units (e.g., 1.50 for £1.50)
            dedupe_id: Unique ID to prevent duplicate deposits

        Returns:
            Updated pot
        """
        amount_minor = convert_amount_to_minor_units(amount)

        data = {
            "source_account_id": source_account_id,
            "amount": str(amount_minor),
            "dedupe_id": dedupe_id,
        }

        response = await self.client._put(f"/pots/{pot_id}/deposit", data=data)
        pot = Pot(**response.json())
        pot._set_client(self.client)
        pot._source_account_id = source_account_id
        return pot

    async def withdraw(
        self,
        pot_id: str,
        destination_account_id: str,
        amount: float | Decimal | str,
        dedupe_id: str,
    ) -> Pot:
        """Withdraw money from a pot.

        Args:
            pot_id: Pot ID
            destination_account_id: Destination account ID
            amount: Amount in major units (e.g., 1.50 for £1.50)
            dedupe_id: Unique ID to prevent duplicate withdrawals

        Returns:
            Updated pot
        """
        amount_minor = convert_amount_to_minor_units(amount)

        data = {
            "destination_account_id": destination_account_id,
            "amount": str(amount_minor),
            "dedupe_id": dedupe_id,
        }

        response = await self.client._put(f"/pots/{pot_id}/withdraw", data=data)
        pot = Pot(**response.json())
        pot._set_client(self.client)
        pot._source_account_id = destination_account_id
        return pot
