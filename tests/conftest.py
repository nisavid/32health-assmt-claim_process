import pytest


@pytest.fixture(scope="session")
def api_url():
    """
    Fixture to provide the base URL for the API.

    Returns:
        str: The base URL for the API.
    """
    return "http://localhost:80"
