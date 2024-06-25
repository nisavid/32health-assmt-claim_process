import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator, List

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter
from pydantic import ValidationError
from redis.asyncio import Redis
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy.sql import func
from sqlmodel import SQLModel, col

from .config import engine, settings
from .models import Claim
from .normalize import normalize_claim
from .schemas import ClaimCreate, ClaimRead, ProviderNetFee

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Context manager for application lifespan. It creates the database tables
    and initializes the rate limiter with Redis.
    """
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
        logger.info("Database tables created")

    # Initialize rate limiter
    redis = Redis(
        host=settings.redis_host,
        port=settings.redis_port,
        db=0,
        encoding="utf-8",
        decode_responses=True,
    )
    await FastAPILimiter.init(redis)
    logger.info("Rate limiter initialized")

    yield
    await redis.close()
    logger.info("Redis connection closed")


app = FastAPI(lifespan=lifespan)


# Dependency to get the session
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency that provides a SQLAlchemy AsyncSession.
    """
    async with AsyncSession(engine) as session:
        yield session


@app.post("/claims", response_model=List[ClaimRead])
async def create_claim(request: Request, session: AsyncSession = Depends(get_session)):
    """
    Create one or more claims. Accepts either a single claim object or a list
    of claim objects.

    Args:
        request (Request): The request object.
        session (AsyncSession): The database session.

    Returns:
        List[ClaimRead]: The created claim(s).
    """
    try:
        raw_data = await request.json()
        # Normalize keys and values
        if isinstance(raw_data, list):
            normalized_data = [normalize_claim(item) for item in raw_data]
        else:
            normalized_data = [normalize_claim(raw_data)]

        claims = []
        for claim_data in normalized_data:
            # Validate normalized data
            claim = ClaimCreate(**claim_data)
            net_fee = (
                claim.provider_fees
                + claim.member_coinsurance
                + claim.member_copay
                - claim.allowed_fees
            )
            db_claim = Claim(
                service_date=claim.service_date,
                submitted_procedure=claim.submitted_procedure,
                quadrant=claim.quadrant,
                plan_group_number=claim.plan_group_number,
                subscriber_number=claim.subscriber_number,
                provider_npi=claim.provider_npi,
                provider_fees=claim.provider_fees,
                member_coinsurance=claim.member_coinsurance,
                member_copay=claim.member_copay,
                allowed_fees=claim.allowed_fees,
                net_fee=net_fee,
            )
            session.add(db_claim)
            try:
                await session.commit()
                await session.refresh(db_claim)
                claims.append(db_claim)
                logger.info(f"Claim {db_claim.id} created successfully")
            except IntegrityError:
                await session.rollback()
                logger.error(
                    f"Claim creation failed: claim {db_claim.id} already exists"
                )
                raise HTTPException(
                    status_code=400, detail="Claim with this ID already exists"
                )
        # Eagerly load attributes for each claim
        for claim in claims:
            await session.refresh(
                claim,
                attribute_names=[
                    attr for attr in claim.__dict__.keys() if not attr.startswith("_")
                ],
            )
        return claims
    except ValidationError as e:
        raise RequestValidationError(e.errors())
    except Exception as e:
        logger.error(f"An unexpected error occurred: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/claims", response_model=List[ClaimRead])
async def get_claims(session: AsyncSession = Depends(get_session)):
    """
    Retrieve all claims.

    Args:
        session (AsyncSession): The database session.

    Returns:
        List[ClaimRead]: The list of all claims.
    """
    try:
        statement = select(Claim).options(selectinload("*"))
        results = await session.execute(statement)
        claims = results.scalars().all()
        logger.info("Claims retrieved successfully")
        return claims
    except Exception as e:
        logger.error(f"An unexpected error occurred: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/claims/{id}", response_model=ClaimRead)
async def get_claim(id: int, session: AsyncSession = Depends(get_session)):
    """
    Retrieve a specific claim by ID.

    Args:
        id (int): The ID of the claim.
        session (AsyncSession): The database session.

    Returns:
        ClaimRead: The requested claim.
    """
    try:
        statement = select(Claim).where(col(Claim.id) == id).options(selectinload("*"))
        result = await session.execute(statement)
        claim = result.scalar_one_or_none()
        if not claim:
            logger.warning(f"Claim with ID {id} not found")
            raise HTTPException(status_code=404, detail="Claim not found")
        logger.info(f"Claim {id} retrieved successfully")
        return claim
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"An unexpected error occurred: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get(
    "/top-provider-npis",
    response_model=List[ProviderNetFee],
    dependencies=[
        Depends(
            RateLimiter(
                times=settings.rate_limit_times, seconds=settings.rate_limit_seconds
            )
        )
    ],
)
async def get_top_provider_npis(session: AsyncSession = Depends(get_session)):
    """
    Retrieve the top 10 provider NPIs by total net fees generated.

    Args:
        session (AsyncSession): The database session.

    Returns:
        List[ProviderNetFee]: The list of top provider NPIs by net fees.
    """
    try:
        statement = (
            select(
                col(Claim.provider_npi), func.sum(Claim.net_fee).label("total_net_fee")
            )
            .group_by(Claim.provider_npi)
            .order_by(func.sum(Claim.net_fee).desc())
            .limit(10)
        )
        results = await session.execute(statement)
        top_providers = results.all()
        logger.info("Top provider NPIs retrieved successfully")
        return [
            {"provider_npi": row.provider_npi, "total_net_fee": row.total_net_fee}
            for row in top_providers
        ]
    except Exception as e:
        logger.error(f"An unexpected error occurred: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
