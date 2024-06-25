from datetime import date
from decimal import Decimal
from typing import Optional

from sqlmodel import Field, SQLModel


class Claim(SQLModel, table=True):
    """
    Database model for a claim.

    Attributes:
        id (Optional[int]): The primary key for the claim.
        service_date (date): The date of the service.
        submitted_procedure (str): The submitted procedure code.
        quadrant (Optional[str]): The quadrant where the procedure was performed.
        plan_group_number (str): The plan/group number associated with the claim.
        subscriber_number (str): The subscriber number associated with the claim.
        provider_npi (str): The National Provider Identifier (NPI) for the provider.
        provider_fees (Decimal): The fees charged by the provider.
        member_coinsurance (Decimal): The coinsurance amount paid by the member.
        member_copay (Decimal): The copay amount paid by the member.
        allowed_fees (Decimal): The allowed fees for the procedure.
        net_fee (Decimal): The net fee calculated for the claim.
    """

    id: Optional[int] = Field(default=None, primary_key=True)
    service_date: date
    submitted_procedure: str = Field(index=True)
    quadrant: Optional[str] = Field(default=None)
    plan_group_number: str = Field(index=True)
    subscriber_number: str = Field(index=True)
    provider_npi: str = Field(index=True)
    provider_fees: Decimal
    member_coinsurance: Decimal
    member_copay: Decimal
    allowed_fees: Decimal
    net_fee: Decimal = Field(default=Decimal("0.0"))
