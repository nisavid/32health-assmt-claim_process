import re
from decimal import Decimal

from dateutil import parser as date_parser


def normalize_key(key: str) -> str:
    """
    Normalize a key by stripping whitespace, replacing '#' with '_number',
    replacing non-word characters with '_', and converting to lowercase.

    Args:
        key (str): The key to be normalized.

    Returns:
        str: The normalized key.
    """
    key = key.strip()
    key = key.replace("#", " number")
    key = re.sub(r"\W+", "_", key)
    key = key.lower()
    return key


def normalize_value(value: str) -> str:
    """
    Normalize a value by stripping whitespace and removing leading '$'.

    Args:
        value (str): The value to be normalized.

    Returns:
        str: The normalized value.
    """
    if isinstance(value, str):
        value = value.strip()
        value = value.lstrip("$")
    return value


def normalize_claim(data: dict) -> dict:
    """
    Normalize a claim dictionary by normalizing its keys and values,
    and converting specific fields to appropriate data types.

    Args:
        data (dict): The claim data to be normalized.

    Returns:
        dict: The normalized claim data.
    """
    data = {normalize_key(k): normalize_value(v) for k, v in data.items()}
    if isinstance(data["service_date"], str):
        try:
            data["service_date"] = date_parser.parse(data["service_date"]).date()
        except (date_parser.ParserError, ValueError):
            pass
    data["provider_fees"] = Decimal(data["provider_fees"])
    data["member_coinsurance"] = Decimal(data["member_coinsurance"])
    data["member_copay"] = Decimal(data["member_copay"])
    data["allowed_fees"] = Decimal(data["allowed_fees"])
    return data
