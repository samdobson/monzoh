"""Tests for mock_data functionality."""

from monzoh.mock_data import (
    MOCK_ACCOUNTS,
    MOCK_BALANCE,
    MOCK_POTS,
    MOCK_TRANSACTIONS,
    MOCK_WEBHOOKS,
    MOCK_WHOAMI,
    get_mock_response,
)


class TestMockConstants:
    """Tests for mock data constants."""

    def test_mock_whoami_structure(self) -> None:
        """Test MOCK_WHOAMI has expected structure."""
        assert "authenticated" in MOCK_WHOAMI
        assert "client_id" in MOCK_WHOAMI
        assert "user_id" in MOCK_WHOAMI
        assert MOCK_WHOAMI["authenticated"] is True
        assert isinstance(MOCK_WHOAMI["client_id"], str)
        assert isinstance(MOCK_WHOAMI["user_id"], str)

    def test_mock_accounts_structure(self) -> None:
        """Test MOCK_ACCOUNTS has expected structure."""
        assert "accounts" in MOCK_ACCOUNTS
        assert isinstance(MOCK_ACCOUNTS["accounts"], list)
        assert len(MOCK_ACCOUNTS["accounts"]) > 0

        account = MOCK_ACCOUNTS["accounts"][0]
        assert "id" in account
        assert "description" in account
        assert "created" in account

    def test_mock_balance_structure(self) -> None:
        """Test MOCK_BALANCE has expected structure."""
        assert "balance" in MOCK_BALANCE
        assert "total_balance" in MOCK_BALANCE
        assert "currency" in MOCK_BALANCE
        assert "spend_today" in MOCK_BALANCE
        assert isinstance(MOCK_BALANCE["balance"], int)
        assert MOCK_BALANCE["currency"] == "GBP"

    def test_mock_transactions_structure(self) -> None:
        """Test MOCK_TRANSACTIONS has expected structure."""
        assert "transactions" in MOCK_TRANSACTIONS
        assert isinstance(MOCK_TRANSACTIONS["transactions"], list)
        assert len(MOCK_TRANSACTIONS["transactions"]) > 0

        transaction = MOCK_TRANSACTIONS["transactions"][0]
        assert "id" in transaction
        assert "amount" in transaction
        assert "created" in transaction
        assert "currency" in transaction
        assert "description" in transaction

    def test_mock_pots_structure(self) -> None:
        """Test MOCK_POTS has expected structure."""
        assert "pots" in MOCK_POTS
        assert isinstance(MOCK_POTS["pots"], list)
        assert len(MOCK_POTS["pots"]) > 0

        pot = MOCK_POTS["pots"][0]
        assert "id" in pot
        assert "name" in pot
        assert "style" in pot
        assert "balance" in pot
        assert "currency" in pot

    def test_mock_webhooks_structure(self) -> None:
        """Test MOCK_WEBHOOKS has expected structure."""
        assert "webhooks" in MOCK_WEBHOOKS
        assert isinstance(MOCK_WEBHOOKS["webhooks"], list)
        assert len(MOCK_WEBHOOKS["webhooks"]) > 0

        webhook = MOCK_WEBHOOKS["webhooks"][0]
        assert "id" in webhook
        assert "account_id" in webhook
        assert "url" in webhook


class TestGetMockResponse:
    """Tests for get_mock_response function."""

    def test_whoami_endpoint(self) -> None:
        """Test /ping/whoami endpoint returns whoami data."""
        result = get_mock_response("/ping/whoami", "GET")
        assert result == MOCK_WHOAMI

    def test_accounts_endpoint(self) -> None:
        """Test /accounts endpoint returns accounts data."""
        result = get_mock_response("/accounts", "GET")
        assert result == MOCK_ACCOUNTS

    def test_balance_endpoint(self) -> None:
        """Test /balance endpoint returns balance data."""
        result = get_mock_response("/balance", "GET")
        assert result == MOCK_BALANCE

    def test_account_balance_endpoint(self) -> None:
        """Test account-specific balance endpoint."""
        result = get_mock_response("/accounts/acc_123/balance", "GET")
        assert result == MOCK_BALANCE

    def test_transactions_endpoint(self) -> None:
        """Test /transactions endpoint returns transactions data."""
        result = get_mock_response("/transactions", "GET")
        assert result == MOCK_TRANSACTIONS

    def test_account_transactions_endpoint(self) -> None:
        """Test account-specific transactions endpoint."""
        result = get_mock_response("/accounts/acc_123/transactions", "GET")
        assert result == MOCK_TRANSACTIONS

    def test_pots_endpoint(self) -> None:
        """Test /pots endpoint returns pots data."""
        result = get_mock_response("/pots", "GET")
        assert result == MOCK_POTS

    def test_webhooks_endpoint(self) -> None:
        """Test /webhooks endpoint returns webhooks data."""
        result = get_mock_response("/webhooks", "GET")
        assert result == MOCK_WEBHOOKS

    def test_single_transaction_endpoint(self) -> None:
        """Test single transaction endpoint."""
        result = get_mock_response("/transactions/tx_123", "GET")
        expected = {"transaction": MOCK_TRANSACTIONS["transactions"][0]}
        assert result == expected

    def test_single_pot_endpoint(self) -> None:
        """Test single pot endpoint."""
        result = get_mock_response("/pots/pot_123", "GET")
        expected = {"pot": MOCK_POTS["pots"][0]}
        assert result == expected

    def test_single_webhook_endpoint(self) -> None:
        """Test single webhook endpoint."""
        result = get_mock_response("/webhooks/webhook_123", "GET")
        expected = {"webhook": MOCK_WEBHOOKS["webhooks"][0]}
        assert result == expected

    def test_unhandled_endpoint(self) -> None:
        """Test unhandled endpoint returns default response."""
        result = get_mock_response("/unknown/endpoint", "POST")

        assert "message" in result
        assert "endpoint" in result
        assert "params" in result
        assert result["message"] == "Mock endpoint not implemented"
        assert result["endpoint"] == "/unknown/endpoint"
        assert result["params"] == {}

    def test_unhandled_endpoint_with_params(self) -> None:
        """Test unhandled endpoint with params."""
        params = {"test": "value", "other": 123}
        result = get_mock_response("/unknown", "GET", params=params)

        assert result["endpoint"] == "/unknown"
        assert result["params"] == params

    def test_transactions_endpoint_excludes_single_transaction(self) -> None:
        """Test that transactions endpoint correctly excludes single transaction."""
        # This should return transactions list
        result = get_mock_response("/accounts/acc_123/transactions", "GET")
        assert result == MOCK_TRANSACTIONS

        # This should return single transaction
        result = get_mock_response("/transactions/tx_123", "GET")
        assert "transaction" in result

    def test_pots_endpoint_excludes_single_pot(self) -> None:
        """Test that pots endpoint logic correctly excludes single pot paths."""
        # This should return pots list
        result = get_mock_response("/pots", "GET")
        assert result == MOCK_POTS

        # This should return single pot
        result = get_mock_response("/pots/pot_123", "GET")
        assert "pot" in result

    def test_webhooks_endpoint_excludes_single_webhook(self) -> None:
        """Test that webhooks endpoint logic correctly excludes single webhook paths."""
        # This should return webhooks list
        result = get_mock_response("/webhooks", "GET")
        assert result == MOCK_WEBHOOKS

        # This should return single webhook
        result = get_mock_response("/webhooks/webhook_123", "GET")
        assert "webhook" in result

    def test_get_mock_response_with_all_kwargs(self) -> None:
        """Test get_mock_response with all possible kwargs."""
        result = get_mock_response(
            "/ping/whoami",
            "GET",
            params={"param": "value"},
            data={"data": "value"},
            json_data={"json": "value"},
        )
        # Should still return whoami data regardless of extra kwargs
        assert result == MOCK_WHOAMI

    def test_method_parameter_ignored(self) -> None:
        """Test that HTTP method parameter doesn't affect response."""
        # Same endpoint with different methods should return same data
        get_result = get_mock_response("/ping/whoami", "GET")
        post_result = get_mock_response("/ping/whoami", "POST")
        put_result = get_mock_response("/ping/whoami", "PUT")

        assert get_result == post_result == put_result == MOCK_WHOAMI
