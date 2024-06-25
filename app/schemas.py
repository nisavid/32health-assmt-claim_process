from datetime import date
from decimal import Decimal
from typing import Annotated, Optional

from pydantic import BaseModel, Field


class ClaimBase(BaseModel):
    """
    Base schema for a claim.

    Attributes:
        service_date (date): The date of the service.
        submitted_procedure (Annotated[str, Field]): The submitted procedure code.
        quadrant (Optional[str]): The quadrant where the procedure was performed.
        plan_group_number (str): The plan/group number associated with the claim.
        subscriber_number (str): The subscriber number associated with the claim.
        provider_npi (Annotated[str, Field]): The National Provider Identifier (NPI) for the provider.
        provider_fees (Annotated[Decimal, Field]): The fees charged by the provider.
        member_coinsurance (Annotated[Decimal, Field]): The coinsurance amount paid by the member.
        member_copay (Annotated[Decimal, Field]): The copay amount paid by the member.
        allowed_fees (Annotated[Decimal, Field]): The allowed fees for the procedure.
    """

    service_date: date
    submitted_procedure: Annotated[str, Field(pattern=r"^D")]
    quadrant: Optional[str] = None
    plan_group_number: str
    subscriber_number: str
    provider_npi: Annotated[
        str, Field(min_length=10, max_length=10, pattern=r"^\d{10}$")
    ]
    provider_fees: Annotated[Decimal, Field(ge=0, decimal_places=2)]
    member_coinsurance: Annotated[Decimal, Field(ge=0, decimal_places=2)]
    member_copay: Annotated[Decimal, Field(ge=0, decimal_places=2)]
    allowed_fees: Annotated[Decimal, Field(ge=0, decimal_places=2)]


class ClaimCreate(ClaimBase):
    """
    Schema for creating a new claim.
    """

    pass


class ClaimRead(ClaimBase):
    """
    Schema for reading a claim.

    Attributes:
        id (int): The primary key for the claim.
        net_fee (Decimal): The net fee calculated for the claim.
    """

    id: int
    net_fee: Decimal

    class Config:
        from_attributes = True


class ProviderNetFee(BaseModel):
    """
    Schema for provider net fee summary.

    Attributes:
        provider_npi (Annotated[str, Field]): The National Provider Identifier (NPI) for the provider.
        total_net_fee (Annotated[Decimal, Field]): The total net fee calculated for the provider.
    """

    provider_npi: Annotated[
        str, Field(min_length=10, max_length=10, pattern=r"^\d{10}$")
    ]
    total_net_fee: Annotated[Decimal, Field(ge=0, decimal_places=2)]
