"""Tests for pots API."""

from typing import Any

from monzoh.models import Pot


class TestPotsAPI:
    """Test PotsAPI."""

    def test_list_pots(
        self,
        monzo_sync_client: Any,
        mock_sync_http_client: Any,
        mock_httpx_response: Any,
        sample_pot: dict[str, Any],
    ) -> None:
        """Test listing pots."""
        mock_response = mock_httpx_response(json_data={"pots": [sample_pot]})
        monzo_sync_client._base_client._get.return_value = mock_response

        pots = monzo_sync_client.pots.list("acc_123")

        assert len(pots) == 1
        assert isinstance(pots[0], Pot)
        assert pots[0].id == sample_pot["id"]
        assert pots[0].name == sample_pot["name"]
        assert pots[0].balance == sample_pot["balance"]

        monzo_sync_client._base_client._get.assert_called_once()
        call_args = monzo_sync_client._base_client._get.call_args
        assert "/pots" in call_args[0][0]
        assert call_args[1]["params"]["current_account_id"] == "acc_123"

    def test_deposit(
        self,
        monzo_sync_client: Any,
        mock_sync_http_client: Any,
        mock_httpx_response: Any,
        sample_pot: dict[str, Any],
    ) -> None:
        """Test depositing into a pot."""
        updated_pot = sample_pot.copy()
        updated_pot["balance"] = 150000  # Increased balance

        mock_response = mock_httpx_response(json_data=updated_pot)
        monzo_sync_client._base_client._put.return_value = mock_response

        pot = monzo_sync_client.pots.deposit(
            pot_id="pot_123",
            source_account_id="acc_123",
            amount=1000,
            dedupe_id="deposit_123",
        )

        assert isinstance(pot, Pot)
        assert pot.balance == 150000

        monzo_sync_client._base_client._put.assert_called_once()
        call_args = monzo_sync_client._base_client._put.call_args
        assert "/pots/pot_123/deposit" in call_args[0][0]
        assert call_args[1]["data"]["source_account_id"] == "acc_123"
        assert call_args[1]["data"]["amount"] == "1000"
        assert call_args[1]["data"]["dedupe_id"] == "deposit_123"

    def test_withdraw(
        self,
        monzo_sync_client: Any,
        mock_sync_http_client: Any,
        mock_httpx_response: Any,
        sample_pot: dict[str, Any],
    ) -> None:
        """Test withdrawing from a pot."""
        updated_pot = sample_pot.copy()
        updated_pot["balance"] = 120000  # Decreased balance

        mock_response = mock_httpx_response(json_data=updated_pot)
        monzo_sync_client._base_client._put.return_value = mock_response

        pot = monzo_sync_client.pots.withdraw(
            pot_id="pot_123",
            destination_account_id="acc_123",
            amount=500,
            dedupe_id="withdraw_123",
        )

        assert isinstance(pot, Pot)
        assert pot.balance == 120000

        monzo_sync_client._base_client._put.assert_called_once()
        call_args = monzo_sync_client._base_client._put.call_args
        assert "/pots/pot_123/withdraw" in call_args[0][0]
        assert call_args[1]["data"]["destination_account_id"] == "acc_123"
        assert call_args[1]["data"]["amount"] == "500"
        assert call_args[1]["data"]["dedupe_id"] == "withdraw_123"
