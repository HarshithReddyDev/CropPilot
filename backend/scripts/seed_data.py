"""Seed script for CropPilot database.

Inserts mock data:
- Farmers
- Farms/Plots with H3 indices in Telangana
- Market prices for Bowenpally mandi
- Government schemes
"""
import asyncio
import uuid
from datetime import date, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.security import hash_password
from db.session import async_session_factory, engine, init_db
from models.disease import DiseaseLog
from models.farm import Farm
from models.market import MarketPrice
from models.plot import Plot
from models.scheme import GovernmentScheme
from models.user import User

TELANGANA_H3_INDICES = [
    "8a1f4a5b6c7ffff",
    "8a1f4a5b6d7ffff",
    "8a1f4a5b6e7ffff",
    "8a1f4a5b6f7ffff",
    "8a1f4a5b707ffff",
]


async def seed_users(db: AsyncSession) -> dict[str, User]:
    users = {}
    for data in [
        {"email": "farmer@croppilot.in", "full_name": "Ramesh Kumar", "role": "farmer", "state": "Telangana", "district": "Medchal-Malkajgiri"},
        {"email": "analyst@croppilot.in", "full_name": "Priya Sharma", "role": "analyst", "state": "Telangana", "district": "Hyderabad"},
        {"email": "admin@croppilot.in", "full_name": "Admin User", "role": "admin", "state": "Telangana", "district": "Hyderabad"},
    ]:
        existing = await db.execute(select(User).where(User.email == data["email"]))
        if existing.scalar_one_or_none():
            user = existing.scalar_one()
        else:
            user = User(
                id=uuid.uuid4(),
                email=data["email"],
                password_hash=hash_password("password123"),
                full_name=data["full_name"],
                role=data["role"],
                state=data.get("state"),
                district=data.get("district"),
                is_verified=True,
            )
            db.add(user)
            await db.flush()
        users[data["email"]] = user
    return users


async def seed_farms_and_plots(db: AsyncSession, farmer: User):
    existing = await db.execute(select(Farm).where(Farm.farmer_id == farmer.id))
    if existing.first():
        return

    farm = Farm(
        id=uuid.uuid4(),
        farmer_id=farmer.id,
        name="Ramesh's Organic Farm",
        description="Family-owned farm growing vegetables and grains",
        address="H.No. 4-56, Bowenpally Village",
        city="Secunderabad",
        state="Telangana",
        total_area_hectares=5.2,
        soil_type="Black Cotton Soil",
        irrigation_type="Drip Irrigation",
    )
    db.add(farm)
    await db.flush()

    for i, h3 in enumerate(TELANGANA_H3_INDICES[:3]):
        plot = Plot(
            id=uuid.uuid4(),
            farm_id=farm.id,
            farmer_id=farmer.id,
            name=f"Plot {chr(65+i)}",
            crop_type="Rice" if i == 0 else ("Cotton" if i == 1 else "Vegetables"),
            crop_variety="BPT-5204" if i == 0 else ("MCU-5" if i == 1 else "Hybrid Mix"),
            sowing_date=datetime(2025, 6, 15) if i == 0 else (datetime(2025, 7, 1) if i == 1 else datetime(2025, 8, 10)),
            expected_harvest_date=datetime(2025, 10, 15) if i == 0 else (datetime(2025, 12, 1) if i == 1 else datetime(2026, 1, 15)),
            area_hectares=2.0 if i == 0 else (1.8 if i == 1 else 1.4),
            h3_index=h3,
            h3_resolution=8,
            soil_ph=7.2,
            soil_moisture=18.5,
            irrigation_type="Drip Irrigation",
            status="active",
        )
        db.add(plot)
    await db.flush()


async def seed_market_prices(db: AsyncSession):
    stmt = select(MarketPrice).limit(1)
    existing = await db.execute(stmt)
    if existing.first():
        return

    prices = [
        {"commodity": "Colacasia", "variety": "Local", "market": "Bowenpally", "district": "Medchal-Malkajgiri", "state": "Telangana", "min_price": 1800, "max_price": 2500, "modal_price": 2200},
        {"commodity": "Tomato", "variety": "Hybrid", "market": "Bowenpally", "district": "Medchal-Malkajgiri", "state": "Telangana", "min_price": 1200, "max_price": 1800, "modal_price": 1500},
        {"commodity": "Brinjal", "variety": "Round", "market": "Bowenpally", "district": "Medchal-Malkajgiri", "state": "Telangana", "min_price": 800, "max_price": 1400, "modal_price": 1100},
        {"commodity": "Rice", "variety": "BPT-5204", "market": "Bowenpally", "district": "Medchal-Malkajgiri", "state": "Telangana", "min_price": 2200, "max_price": 2800, "modal_price": 2500},
        {"commodity": "Cotton", "variety": "MCU-5", "market": "Bowenpally", "district": "Medchal-Malkajgiri", "state": "Telangana", "min_price": 5500, "max_price": 6800, "modal_price": 6200},
        {"commodity": "Maize", "variety": "Hybrid", "market": "Bowenpally", "district": "Medchal-Malkajgiri", "state": "Telangana", "min_price": 1500, "max_price": 2100, "modal_price": 1800},
        {"commodity": "Chilli", "variety": "Dry", "market": "Bowenpally", "district": "Medchal-Malkajgiri", "state": "Telangana", "min_price": 8000, "max_price": 12000, "modal_price": 10000},
        {"commodity": "Groundnut", "variety": "Pod", "market": "Bowenpally", "district": "Medchal-Malkajgiri", "state": "Telangana", "min_price": 3500, "max_price": 4500, "modal_price": 4000},
    ]

    for p in prices:
        for days_ago in range(7):
            price = MarketPrice(
                id=uuid.uuid4(),
                commodity=p["commodity"],
                variety=p["variety"],
                market=p["market"],
                district=p["district"],
                state=p["state"],
                min_price=p["min_price"] + (days_ago * 20),
                max_price=p["max_price"] + (days_ago * 30),
                modal_price=p["modal_price"] + (days_ago * 25),
                arrival_date=date.today() - timedelta(days=days_ago),
                source="AGMARKNET",
            )
            db.add(price)
    await db.flush()


async def seed_government_schemes(db: AsyncSession):
    stmt = select(GovernmentScheme).limit(1)
    existing = await db.execute(stmt)
    if existing.first():
        return

    schemes = [
        GovernmentScheme(
            id=uuid.uuid4(),
            scheme_name="Pradhan Mantri Fasal Bima Yojana",
            scheme_code="PMFBY",
            description="Comprehensive crop insurance covering all stages of crop growth. Provides financial support against crop loss due to natural calamities, pests, and diseases.",
            ministry="Ministry of Agriculture",
            state_jurisdiction="Telangana",
            eligibility_criteria="All farmers growing notified crops in notified areas. Both loanee and non-loanee farmers are eligible.",
            benefits="Insurance coverage for sum insured, premium subsidy of up to 80% for small farmers.",
            application_process="Apply through local bank branches, insurance company agents, or online portal.",
            documents_required="Land records, bank account details, Aadhaar card, previous crop details.",
            category="Insurance",
            tags=["crop insurance", "risk management", "subsidy"],
            is_active=True,
        ),
        GovernmentScheme(
            id=uuid.uuid4(),
            scheme_name="PM-KISAN Samman Nidhi",
            scheme_code="PMKSN",
            description="Income support scheme providing Rs.6,000 per year to landholding farmer families, payable in three equal installments.",
            ministry="Ministry of Agriculture",
            state_jurisdiction="Telangana",
            eligibility_criteria="All landholding farmer families with cultivable land in their name.",
            benefits="Rs.6,000 per year direct cash transfer to bank account.",
            application_process="Apply through local agriculture office, CSC centers, or online PM-KISAN portal.",
            documents_required="Aadhaar card, land records, bank account details.",
            category="Income Support",
            tags=["income support", "cash transfer", "direct benefit"],
            is_active=True,
        ),
        GovernmentScheme(
            id=uuid.uuid4(),
            scheme_name="Rythu Bandhu Scheme",
            scheme_code="RB-TG",
            description="Telangana government's investment support scheme providing Rs.10,000 per acre per year to farmers for crop investment.",
            ministry="Government of Telangana",
            state_jurisdiction="Telangana",
            eligibility_criteria="All farmers in Telangana state with agricultural land.",
            benefits="Rs.10,000 per acre per year (Rs.5,000 per season) investment support.",
            application_process="Farmers are automatically enrolled based on land records. Updates through village agriculture officers.",
            documents_required="Land records (pahani), Aadhaar card.",
            category="Investment Support",
            tags=["investment support", "Telangana", "input subsidy"],
            is_active=True,
        ),
        GovernmentScheme(
            id=uuid.uuid4(),
            scheme_name="Soil Health Card Scheme",
            scheme_code="SHC",
            description="Provides soil health cards to farmers with nutrient status and recommendations for their farms.",
            ministry="Ministry of Agriculture",
            state_jurisdiction="Telangana",
            eligibility_criteria="All farmers are eligible.",
            benefits="Free soil testing, customized fertilizer recommendations, improved crop productivity.",
            application_process="Request soil sample collection through local agriculture office or Kissan call center.",
            documents_required="Land records, farmer details.",
            category="Soil Health",
            tags=["soil testing", "fertility", "nutrient management"],
            is_active=True,
        ),
        GovernmentScheme(
            id=uuid.uuid4(),
            scheme_name="National Agriculture Market (e-NAM)",
            scheme_code="eNAM",
            description="Pan-India electronic trading portal connecting APMC mandis to create a unified national market.",
            ministry="Ministry of Agriculture",
            state_jurisdiction="Telangana",
            eligibility_criteria:"All farmers, traders, and commission agents registered with APMC.",
            benefits="Better price discovery, transparent auction, online payment, single license for multiple mandis.",
            application_process="Register through local APMC mandi or online e-NAM portal.",
            documents_required="Aadhaar card, bank account, land records, trader license.",
            category="Market",
            tags=["e-trading", "mandi", "price discovery", "marketing"],
            is_active=True,
        ),
    ]

    for scheme in schemes:
        existing = await db.execute(
            select(GovernmentScheme).where(GovernmentScheme.scheme_code == scheme.scheme_code)
        )
        if not existing.scalar_one_or_none():
            db.add(scheme)
    await db.flush()


async def seed_all():
from db.session import init_db as ensure_tables
async with engine.begin() as conn:
    await conn.run_sync(lambda _: None)

    async with async_session_factory() as db:
        users = await seed_users(db)
        await seed_farms_and_plots(db, users["farmer@croppilot.in"])
        await seed_market_prices(db)
        await seed_government_schemes(db)
        await db.commit()
        print("Database seeded successfully!")


if __name__ == "__main__":
    asyncio.run(seed_all())
