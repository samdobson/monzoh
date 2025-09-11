import nox
from nox import Session

nox.options.sessions = ["tests", "lint", "mypy", "docs"]


@nox.session(python=["3.10", "3.11", "3.12", "3.13"])
def tests(session: Session) -> None:
    """Run the test suite.

    Args:
        session: The nox session object.
    """
    session.install(".[dev]")
    session.run("pytest", *session.posargs)


@nox.session(python="3.10")
def lint(session: Session) -> None:
    """Run the linter.

    Args:
        session: The nox session object.
    """
    session.install(".[dev]")
    session.run("ruff", "check", ".")
    session.run("black", "--check", ".")


@nox.session(python="3.10")
def mypy(session: Session) -> None:
    """Run mypy.

    Args:
        session: The nox session object.
    """
    session.install(".[dev]")
    session.run("mypy", "src/monzoh")


@nox.session(python="3.10")
def format(session: Session) -> None:
    """Format code with black and ruff.

    Args:
        session: The nox session object.
    """
    session.install(".[dev]")
    session.run("black", ".")
    session.run("ruff", "check", "--fix", ".")


@nox.session(python="3.10")
def coverage(session: Session) -> None:
    """Generate coverage report.

    Args:
        session: The nox session object.
    """
    session.install(".[dev]")
    session.run(
        "pytest",
        "--cov=monzoh",
        "--cov-report=html",
        "--cov-report=term",
        "--cov-report=lcov",
    )


@nox.session(python="3.10")
def docs(session: Session) -> None:
    """Check docstring quality and coverage.

    Args:
        session: The nox session object.
    """
    session.install(".[dev]")
    session.run("pydocstyle", "src/monzoh")
    session.run("interrogate", "src/monzoh", "--verbose")


@nox.session(python="3.10")
def docs_strict(session: Session) -> None:
    """Check docstring quality with strict argument checking.

    Args:
        session: The nox session object.
    """
    session.install(".[dev]")
    session.run("pydocstyle", "src/monzoh")
    session.run("interrogate", "src/monzoh", "--verbose")
    session.run("pydoclint", "src/monzoh")
