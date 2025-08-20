[![PyPI version](https://badge.fury.io/py/monzoh.svg)](https://badge.fury.io/py/monzoh)
[![Python versions](https://img.shields.io/pypi/pyversions/monzoh.svg)](https://pypi.org/project/monzoh/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

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

