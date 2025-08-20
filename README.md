![Package version](https://img.shields.io/pypi/v/monzoh)
![Python versions](https://img.shields.io/pypi/pyversions/monzoh.svg)
![License](https://img.shields.io/pypi/l/monzoh)
![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)
![py.typed](https://img.shields.io/badge/py-typed-FFD43B)

![Hero](hero.png)

A Python library for the Monzo Developer API.

📖 [View Full Documentation](https://sjd333-organization.mintlify.app/docs/introduction)


## Features

- 📦 Trusted PyPI publishing
- 🌐 Full Monzo API coverage
- 🔐 Simple OAuth2 authentication flow
- 🔒 Type-safe with Pydantic models
- ✅ Well-tested and documented
- ⚠️  Comprehensive error handling

## Installation

```bash
uv add monzoh
```

## Quick Start

```python
from monzoh import MonzoClient

# Initialize client
client = MonzoClient()

# List accounts
accounts = client.accounts.list()

# Get account balance
balance = client.accounts.get_balance(account_id="acc_123")

# List transactions
transactions = client.transactions.list(account_id="acc_123")
```

