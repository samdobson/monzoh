"""Tests for pots API."""

import uuid
from decimal import Decimal
from typing import Any
from unittest.mock import patch

from monzoh.models import Pot


class TestPotsAPI:
    """Test PotsAPI."""

    def test_list_pots(
        self,
        monzo_client: Any,
        mock_response: Any,
        sample_pot: dict[str, Any],
    ) -> None:
        """Test listing pots.

        Args:
            monzo_client: Monzo client fixture.
            mock_response: Mock response fixture.
            sample_pot: Sample pot data fixture.
        """
        mock_response = mock_response(json_data={"pots": [sample_pot]})
        monzo_client._base_client._get.return_value = mock_response

        pots = monzo_client.pots.list("acc_123")

        assert len(pots) == 1
        assert isinstance(pots[0], Pot)
        assert pots[0].id == sample_pot["id"]
        assert pots[0].name == sample_pot["name"]
        assert pots[0].balance == Decimal("1337.00")

        monzo_client._base_client._get.assert_called_once()
        call_args = monzo_client._base_client._get.call_args
        assert "/pots" in call_args[0][0]
        assert call_args[1]["params"]["current_account_id"] == "acc_123"

    def test_deposit(
        self,
        monzo_client: Any,
        mock_response: Any,
        sample_pot: dict[str, Any],
    ) -> None:
        """Test depositing into a pot.

        Args:
            monzo_client: Monzo client fixture.
            mock_response: Mock response fixture.
            sample_pot: Sample pot data fixture.
        """
        updated_pot = sample_pot.copy()
        updated_pot["balance"] = 150000

        mock_response = mock_response(json_data=updated_pot)
        monzo_client._base_client._put.return_value = mock_response

        pot = monzo_client.pots.deposit(
            pot_id="pot_123",
            source_account_id="acc_123",
            amount=10.00,
            dedupe_id="deposit_123",
        )

        assert isinstance(pot, Pot)
        assert pot.balance == Decimal("1500.00")

        monzo_client._base_client._put.assert_called_once()
        call_args = monzo_client._base_client._put.call_args
        assert "/pots/pot_123/deposit" in call_args[0][0]
        assert call_args[1]["data"]["source_account_id"] == "acc_123"
        assert call_args[1]["data"]["amount"] == "1000"
        assert call_args[1]["data"]["dedupe_id"] == "deposit_123"

    def test_withdraw(
        self,
        monzo_client: Any,
        mock_response: Any,
        sample_pot: dict[str, Any],
    ) -> None:
        """Test withdrawing from a pot.

        Args:
            monzo_client: Monzo client fixture.
            mock_response: Mock response fixture.
            sample_pot: Sample pot data fixture.
        """
        updated_pot = sample_pot.copy()
        updated_pot["balance"] = 120000

        mock_response = mock_response(json_data=updated_pot)
        monzo_client._base_client._put.return_value = mock_response

        pot = monzo_client.pots.withdraw(
            pot_id="pot_123",
            destination_account_id="acc_123",
            amount=5.00,
            dedupe_id="withdraw_123",
        )

        assert isinstance(pot, Pot)
        assert pot.balance == Decimal("1200.00")

        monzo_client._base_client._put.assert_called_once()
        call_args = monzo_client._base_client._put.call_args
        assert "/pots/pot_123/withdraw" in call_args[0][0]
        assert call_args[1]["data"]["destination_account_id"] == "acc_123"
        assert call_args[1]["data"]["amount"] == "500"
        assert call_args[1]["data"]["dedupe_id"] == "withdraw_123"

    def test_deposit_auto_dedupe_id(
        self,
        monzo_client: Any,
        mock_response: Any,
        sample_pot: dict[str, Any],
    ) -> None:
        """Test depositing into a pot with auto-generated dedupe_id.

        Args:
            monzo_client: Monzo client fixture.
            mock_response: Mock response fixture.
            sample_pot: Sample pot data fixture.
        """
        updated_pot = sample_pot.copy()
        updated_pot["balance"] = 150000

        mock_response = mock_response(json_data=updated_pot)
        monzo_client._base_client._put.return_value = mock_response

        with patch("monzoh.api.pots.uuid.uuid4") as mock_uuid:
            mock_uuid.return_value = uuid.UUID("12345678-1234-5678-9012-123456789abc")

            pot = monzo_client.pots.deposit(
                pot_id="pot_123",
                source_account_id="acc_123",
                amount=1000,
            )

        assert isinstance(pot, Pot)
        assert pot.balance == 1500

        monzo_client._base_client._put.assert_called_once()
        call_args = monzo_client._base_client._put.call_args
        assert "/pots/pot_123/deposit" in call_args[0][0]
        assert call_args[1]["data"]["source_account_id"] == "acc_123"
        assert call_args[1]["data"]["amount"] == "100000"
        assert (
            call_args[1]["data"]["dedupe_id"] == "12345678-1234-5678-9012-123456789abc"
        )

    def test_withdraw_auto_dedupe_id(
        self,
        monzo_client: Any,
        mock_response: Any,
        sample_pot: dict[str, Any],
    ) -> None:
        """Test withdrawing from a pot with auto-generated dedupe_id.

        Args:
            monzo_client: Monzo client fixture.
            mock_response: Mock response fixture.
            sample_pot: Sample pot data fixture.
        """
        updated_pot = sample_pot.copy()
        updated_pot["balance"] = 120000

        mock_response = mock_response(json_data=updated_pot)
        monzo_client._base_client._put.return_value = mock_response

        with patch("monzoh.api.pots.uuid.uuid4") as mock_uuid:
            mock_uuid.return_value = uuid.UUID("87654321-4321-8765-2109-987654321cba")

            pot = monzo_client.pots.withdraw(
                pot_id="pot_123",
                destination_account_id="acc_123",
                amount=500,
            )

        assert isinstance(pot, Pot)
        assert pot.balance == 1200

        monzo_client._base_client._put.assert_called_once()
        call_args = monzo_client._base_client._put.call_args
        assert "/pots/pot_123/withdraw" in call_args[0][0]
        assert call_args[1]["data"]["destination_account_id"] == "acc_123"
        assert call_args[1]["data"]["amount"] == "50000"
        assert (
            call_args[1]["data"]["dedupe_id"] == "87654321-4321-8765-2109-987654321cba"
        )
