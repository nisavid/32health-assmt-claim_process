import csv
from decimal import Decimal

import httpx
import pytest
from fastapi import status


# Helper function to convert CSV to JSON
def csv_to_json(csv_file_path):
    """
    Convert a CSV file to a list of dictionaries.

    Args:
        csv_file_path (str): The path to the CSV file.

    Returns:
        list: A list of dictionaries where each dictionary represents a row in the CSV file.
    """
    with open(csv_file_path, mode="r") as file:
        reader = csv.DictReader(file)
        return [row for row in reader]


@pytest.mark.asyncio
async def test_post_claim_normalized(api_url):
    """
    Test posting a single claim with normalized field names and valid values.

    This test sends a POST request to create a new claim, verifies the response,
    and then uses GET requests to verify the claim was created correctly.

    Args:
        api_url (str): The base URL of the API.
    """
    async with httpx.AsyncClient(base_url=api_url) as client:
        response = await client.get("/claims")
        assert response.status_code == status.HTTP_200_OK
        claims = response.json()
        n_claims_before = len(claims)

        claim_data = {
            "service_date": "2024-06-24",
            "submitted_procedure": "D1234",
            "quadrant": "UR",
            "plan_group_number": "ABC123",
            "subscriber_number": "SUB123456",
            "provider_npi": "1234567890",
            "provider_fees": 100.0,
            "member_coinsurance": 20.0,
            "member_copay": 10.0,
            "allowed_fees": 50.0,
        }
        response = await client.post("/claims", json=claim_data)
        assert response.status_code == status.HTTP_200_OK
        claims = response.json()
        assert len(claims) == 1
        claim = claims[0]
        assert claim["provider_npi"] == "1234567890"
        assert Decimal(claim["net_fee"]) == Decimal("80.0")

        # Verify with GET requests
        response = await client.get(f"/claims/{claim['id']}")
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == claim

        response = await client.get("/claims")
        assert response.status_code == status.HTTP_200_OK
        claims = response.json()
        assert len(claims) == n_claims_before + 1
        assert claims[-1] == claim


@pytest.mark.asyncio
async def test_post_claim_non_normalized(api_url):
    """
    Test posting a single claim with non-normalized field names and valid values.

    This test sends a POST request to create a new claim with non-normalized field names,
    verifies the response, and then uses GET requests to verify the claim was created correctly.

    Args:
        api_url (str): The base URL of the API.
    """
    async with httpx.AsyncClient(base_url=api_url) as client:
        response = await client.get("/claims")
        assert response.status_code == status.HTTP_200_OK
        claims = response.json()
        n_claims_before = len(claims)

        claim_data = {
            " Service Date ": "2024-06-24",
            "Submitted Procedure": "D1234",
            "Quadrant": "UR",
            "Plan/Group #": "ABC123",
            "Subscriber#": "SUB123456",
            "Provider NPI": "2345678901",
            "provider fees": 100.0,
            "member CoInsurance": 20.0,
            "member coPay": 10.0,
            "Allowed Fees": 50.0,
        }
        response = await client.post("/claims", json=claim_data)
        assert response.status_code == status.HTTP_200_OK
        claims = response.json()
        assert len(claims) == 1
        claim = claims[0]
        assert claim["provider_npi"] == "2345678901"
        assert Decimal(claim["net_fee"]) == Decimal("80.0")

        # Verify with GET requests
        response = await client.get(f"/claims/{claim['id']}")
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == claim

        response = await client.get("/claims")
        assert response.status_code == status.HTTP_200_OK
        claims = response.json()
        assert len(claims) == n_claims_before + 1
        assert claims[-1] == claim


@pytest.mark.asyncio
async def test_post_claim_invalid_values(api_url):
    """
    Test posting a single claim with normalized field names and invalid values.

    This test sends a POST request to create a new claim with invalid field values,
    verifies the response, and then uses GET requests to verify that the claim was not created.

    Args:
        api_url (str): The base URL of the API.
    """
    async with httpx.AsyncClient(base_url=api_url) as client:
        response = await client.get("/claims")
        assert response.status_code == status.HTTP_200_OK
        claims = response.json()
        n_claims_before = len(claims)

        claim_data = {
            "service_date": "invalid-date",
            "submitted_procedure": "1234",
            "quadrant": "UR",
            "plan_group_number": "ABC123",
            "subscriber_number": "SUB123456",
            "provider_npi": "4567890123",
            "provider_fees": -100.0,
            "member_coinsurance": 20.0,
            "member_copay": 10.0,
            "allowed_fees": 50.0,
        }
        response = await client.post("/claims", json=claim_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

        response = await client.get("/claims")
        assert response.status_code == status.HTTP_200_OK
        claims = response.json()
        assert len(claims) == n_claims_before


@pytest.mark.asyncio
async def test_post_claims_from_csv(api_url):
    """
    Test posting multiple claims from a CSV file.

    This test reads claims data from a CSV file, sends a POST request to create the claims,
    verifies the response, and then uses GET requests to verify that the claims were created correctly.

    Args:
        api_url (str): The base URL of the API.
    """
    async with httpx.AsyncClient(base_url=api_url) as client:
        response = await client.get("/claims")
        assert response.status_code == status.HTTP_200_OK
        claims = response.json()
        n_claims_before = len(claims)

        claims_data = csv_to_json("example/claim_1234.csv")
        response = await client.post("/claims", json=claims_data)
        assert response.status_code == status.HTTP_200_OK

        response = await client.get("/claims")
        assert response.status_code == status.HTTP_200_OK
        claims = response.json()
        assert len(claims) == n_claims_before + len(claims_data)

        response = await client.get("/top-provider-npis")
        assert response.status_code == status.HTTP_200_OK
        top_providers = response.json()
        assert len(top_providers) <= 10


@pytest.mark.asyncio
async def test_post_claims_multiple_npis(api_url):
    """
    Test posting multiple claims with different NPIs.

    This test sends a POST request to create multiple claims with different NPIs,
    verifies the response, and then uses GET requests to verify that the claims were created correctly.
    Finally, it verifies that the correct top 10 NPIs are returned from the /top-provider-npis endpoint.

    Args:
        api_url (str): The base URL of the API.
    """
    async with httpx.AsyncClient(base_url=api_url) as client:
        response = await client.get("/claims")
        assert response.status_code == status.HTTP_200_OK
        claims = response.json()
        n_claims_before = len(claims)

        claims_data = [
            {
                "service_date": "2024-06-24",
                "submitted_procedure": "D1234",
                "quadrant": "UR",
                "plan_group_number": "ABC123",
                "subscriber_number": f"SUB{i:02d}01234",
                "provider_npi": f"98765432{i:02d}",
                "provider_fees": str(Decimal("1000") + 10 * i),
                "member_coinsurance": str(Decimal("20")),
                "member_copay": str(Decimal("10")),
                "allowed_fees": str(Decimal("50")),
            }
            for i in range(15)
        ]
        response = await client.post("/claims", json=claims_data)
        assert response.status_code == status.HTTP_200_OK
        claims = response.json()
        assert len(claims) == len(claims_data)

        response = await client.get("/claims")
        assert response.status_code == status.HTTP_200_OK
        claims = response.json()
        assert len(claims) == n_claims_before + len(claims_data)

        response = await client.get("/top-provider-npis")
        assert response.status_code == status.HTTP_200_OK
        top_providers = response.json()
        assert len(top_providers) == 10
        assert top_providers[0]["provider_npi"] == "9876543214"
        assert (
            Decimal(top_providers[0]["total_net_fee"])
            == Decimal("1000") + 140 + 20 + 10 - 50
        )
