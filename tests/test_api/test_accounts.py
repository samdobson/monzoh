"""Tests for accounts API."""

from typing import Any

from monzoh.models import Account, Balance


class TestAccountsAPI:
    """Test AccountsAPI."""

    def test_list_accounts(
        self,
        monzo_client: Any,
        mock_http_client: Any,
        mock_response: Any,
        sample_account: dict[str, Any],
    ) -> None:
        """Test listing accounts."""
        mock_response = mock_response(json_data={"accounts": [sample_account]})
        monzo_client._base_client._get.return_value = mock_response

        accounts = monzo_client.accounts.list()

        assert len(accounts) == 1
        assert isinstance(accounts[0], Account)
        assert accounts[0].id == sample_account["id"]
        assert accounts[0].description == sample_account["description"]

        monzo_client._base_client._get.assert_called_once()
        call_args = monzo_client._base_client._get.call_args
        assert "/accounts" in call_args[0][0]

    def test_list_accounts_with_filter(
        self,
        monzo_client: Any,
        mock_http_client: Any,
        mock_response: Any,
        sample_account: dict[str, Any],
    ) -> None:
        """Test listing accounts with account type filter."""
        mock_response = mock_response(json_data={"accounts": [sample_account]})
        monzo_client._base_client._get.return_value = mock_response

        accounts = monzo_client.accounts.list(account_type="uk_retail")

        assert len(accounts) == 1

        monzo_client._base_client._get.assert_called_once()
        call_args = monzo_client._base_client._get.call_args
        assert call_args[1]["params"]["account_type"] == "uk_retail"

    def test_get_balance(
        self,
        monzo_client: Any,
        mock_http_client: Any,
        mock_response: Any,
        sample_balance: dict[str, Any],
    ) -> None:
        """Test getting account balance."""
        mock_response = mock_response(json_data=sample_balance)
        monzo_client._base_client._get.return_value = mock_response

        balance = monzo_client.accounts.get_balance("acc_123")

        assert isinstance(balance, Balance)
        assert balance.balance == sample_balance["balance"]
        assert balance.total_balance == sample_balance["total_balance"]
        assert balance.currency == sample_balance["currency"]
        assert balance.spend_today == sample_balance["spend_today"]

        monzo_client._base_client._get.assert_called_once()
        call_args = monzo_client._base_client._get.call_args
        assert "/balance" in call_args[0][0]
        assert call_args[1]["params"]["account_id"] == "acc_123"
