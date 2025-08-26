![Package version](https://img.shields.io/pypi/v/monzoh)
![Python versions](https://img.shields.io/pypi/pyversions/monzoh.svg)
![License](https://img.shields.io/pypi/l/monzoh)
![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)
![py.typed](https://img.shields.io/badge/py-typed-FFD43B)
[![Coverage Status](https://coveralls.io/repos/github/samdobson/monzoh/badge.svg?branch=main)](https://coveralls.io/github/samdobson/monzoh?branch=main)

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

1. Create an OAuth2 client on the [Monzo Developers Portal](https://developers.monzo.com/). *Redirect URL* must be `http://localhost:8080/callback` and *Confidentiality* must be `Confidential`.
1. Run `monzo-auth` and complete the login flow.
1. Authorise access on the Monzo app.

You can now.

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

