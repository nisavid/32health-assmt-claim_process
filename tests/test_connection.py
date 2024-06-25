import httpx
import pytest
from fastapi import status


@pytest.mark.asyncio
async def test_connection(api_url):
    """
    Test the connection to the API server.

    This test sends a GET request to the root URL and verifies that the server
    responds with a 404 Not Found status code, indicating that the server is up
    and running and the root endpoint does not exist.

    Args:
        api_url (str): The base URL of the API.

    Asserts:
        The response status code is 404 Not Found.
    """
    async with httpx.AsyncClient(base_url=api_url) as client:
        response = await client.get("/")
        assert response.status_code == status.HTTP_404_NOT_FOUND
