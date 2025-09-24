"""Tests for async pots API."""

from decimal import Decimal
from typing import Any, cast
from unittest.mock import Mock  # noqa: TC003

import pytest

from monzoh.api.async_pots import AsyncPotsAPI
from monzoh.core.async_base import BaseAsyncClient
from monzoh.models import Pot


class TestAsyncPotsAPI:
    """Test async pots API."""

    @pytest.fixture
    def pots_api(self, mock_async_base_client: BaseAsyncClient) -> AsyncPotsAPI:
        """Create async pots API instance.

        Args:
            mock_async_base_client: Mock async base client fixture.

        Returns:
            AsyncPotsAPI instance.
        """
        return AsyncPotsAPI(mock_async_base_client)

    @pytest.mark.asyncio
    async def test_list_pots(
        self,
        pots_api: AsyncPotsAPI,
        mock_async_base_client: BaseAsyncClient,
        sample_pot: dict[str, Any],
    ) -> None:
        """Test listing pots.

        Args:
            pots_api: Async pots API fixture.
            mock_async_base_client: Mock async base client fixture.
            sample_pot: Sample pot data fixture.
        """
        cast("Mock", mock_async_base_client._get).return_value.json.return_value = {
            "pots": [sample_pot]
        }

        pots = await pots_api.list("acc_123")

        cast("Mock", mock_async_base_client._get).assert_called_once_with(
            "/pots", params={"current_account_id": "acc_123"}
        )
        assert len(pots) == 1
        assert isinstance(pots[0], Pot)
        assert pots[0].id == sample_pot["id"]
        assert pots[0].name == sample_pot["name"]
        assert pots[0].balance == Decimal("1337.00")

    @pytest.mark.asyncio
    async def test_deposit(
        self,
        pots_api: AsyncPotsAPI,
        mock_async_base_client: BaseAsyncClient,
        sample_pot: dict[str, Any],
    ) -> None:
        """Test depositing into a pot.

        Args:
            pots_api: Async pots API fixture.
            mock_async_base_client: Mock async base client fixture.
            sample_pot: Sample pot data fixture.
        """
        updated_pot = sample_pot.copy()
        updated_pot["balance"] = 150000

        cast(
            "Mock", mock_async_base_client._put
        ).return_value.json.return_value = updated_pot

        pot = await pots_api.deposit(
            pot_id="pot_123",
            source_account_id="acc_123",
            amount=10.00,
            dedupe_id="deposit_123",
        )

        cast("Mock", mock_async_base_client._put).assert_called_once_with(
            "/pots/pot_123/deposit",
            data={
                "source_account_id": "acc_123",
                "amount": "1000",
                "dedupe_id": "deposit_123",
            },
        )
        assert isinstance(pot, Pot)
        assert pot.balance == Decimal("1500.00")

    @pytest.mark.asyncio
    async def test_withdraw(
        self,
        pots_api: AsyncPotsAPI,
        mock_async_base_client: BaseAsyncClient,
        sample_pot: dict[str, Any],
    ) -> None:
        """Test withdrawing from a pot.

        Args:
            pots_api: Async pots API fixture.
            mock_async_base_client: Mock async base client fixture.
            sample_pot: Sample pot data fixture.
        """
        updated_pot = sample_pot.copy()
        updated_pot["balance"] = 120000

        cast(
            "Mock", mock_async_base_client._put
        ).return_value.json.return_value = updated_pot

        pot = await pots_api.withdraw(
            pot_id="pot_123",
            destination_account_id="acc_123",
            amount=5.00,
            dedupe_id="withdraw_123",
        )

        cast("Mock", mock_async_base_client._put).assert_called_once_with(
            "/pots/pot_123/withdraw",
            data={
                "destination_account_id": "acc_123",
                "amount": "500",
                "dedupe_id": "withdraw_123",
            },
        )
        assert isinstance(pot, Pot)
        assert pot.balance == Decimal("1200.00")
