"""Pots API endpoints."""

import uuid

from ..core import BaseSyncClient
from ..models import Pot, PotsResponse


class PotsAPI:
    """Pots API client."""

    def __init__(self, client: BaseSyncClient) -> None:
        """Initialize pots API.

        Args:
            client: Base API client
        """
        self.client = client

    def list(self, current_account_id: str) -> list[Pot]:
        """List pots for an account.

        Args:
            current_account_id: Account ID

        Returns:
            List of pots
        """
        params = {"current_account_id": current_account_id}

        response = self.client._get("/pots", params=params)
        pots_response = PotsResponse(**response.json())
        return pots_response.pots

    def deposit(
        self,
        pot_id: str,
        source_account_id: str,
        amount: int,
        dedupe_id: str | None = None,
    ) -> Pot:
        """Deposit money into a pot.

        Args:
            pot_id: Pot ID
            source_account_id: Source account ID
            amount: Amount in minor units (e.g., pennies)
            dedupe_id: Unique ID to prevent duplicate deposits
                (auto-generated if not provided)

        Returns:
            Updated pot
        """
        if dedupe_id is None:
            dedupe_id = str(uuid.uuid4())

        data = {
            "source_account_id": source_account_id,
            "amount": str(amount),
            "dedupe_id": dedupe_id,
        }

        response = self.client._put(f"/pots/{pot_id}/deposit", data=data)
        return Pot(**response.json())

    def withdraw(
        self,
        pot_id: str,
        destination_account_id: str,
        amount: int,
        dedupe_id: str | None = None,
    ) -> Pot:
        """Withdraw money from a pot.

        Args:
            pot_id: Pot ID
            destination_account_id: Destination account ID
            amount: Amount in minor units (e.g., pennies)
            dedupe_id: Unique ID to prevent duplicate withdrawals
                (auto-generated if not provided)

        Returns:
            Updated pot
        """
        if dedupe_id is None:
            dedupe_id = str(uuid.uuid4())

        data = {
            "destination_account_id": destination_account_id,
            "amount": str(amount),
            "dedupe_id": dedupe_id,
        }

        response = self.client._put(f"/pots/{pot_id}/withdraw", data=data)
        return Pot(**response.json())
