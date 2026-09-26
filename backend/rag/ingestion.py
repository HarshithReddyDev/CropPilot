import json

from rag.pipeline import rag_pipeline


async def ingest_schemes_from_json(filepath: str):
    with open(filepath) as f:
        schemes = json.load(f)

    for scheme in schemes:
        await rag_pipeline.ingest_scheme(scheme)

    return len(schemes)


async def _seed_relational_rows(schemes: list[dict]) -> int:
    """Idempotent relational seed so list/fallback reads work.

    Vector ingestion alone leaves government_schemes empty, which
    silently breaks schemes_list and the retrieval fallback.
    """
    from sqlalchemy import select

    from db.session import async_session_factory
    from models.scheme import GovernmentScheme

    inserted = 0
    async with async_session_factory() as session:
        for scheme in schemes:
            existing = await session.execute(
                select(GovernmentScheme.id).where(
                    GovernmentScheme.scheme_name == scheme["scheme_name"]
                )
            )
            if existing.scalar_one_or_none() is not None:
                continue
            session.add(
                GovernmentScheme(
                    scheme_name=scheme["scheme_name"],
                    scheme_code=scheme.get("id"),
                    description=scheme.get("description", ""),
                    ministry=scheme.get("ministry"),
                    state_jurisdiction=scheme.get("state_jurisdiction"),
                    benefits=scheme.get("benefits"),
                    category=scheme.get("category"),
                    is_active=True,
                )
            )
            inserted += 1
        await session.commit()
    return inserted


async def ingest_scheme_data():
    schemes = [
        {
            "id": "s1",
            "scheme_name": "Pradhan Mantri Fasal Bima Yojana",
            "description": "Comprehensive crop insurance scheme covering all stages of crop growth. "
            "Provides financial support to farmers suffering crop loss/damage due to natural calamities.",
            "benefits": "Insurance coverage for crops, premium subsidy up to 80%",
            "state_jurisdiction": "Telangana",
            "category": "Insurance",
            "ministry": "Ministry of Agriculture",
        },
        {
            "id": "s2",
            "scheme_name": "PM-KISAN Samman Nidhi",
            "description": "Income support scheme providing financial benefit of Rs.6000/year "
            "to landholding farmer families, payable in three equal installments.",
            "benefits": "Rs.6000 per year direct cash transfer",
            "state_jurisdiction": "Telangana",
            "category": "Income Support",
            "ministry": "Ministry of Agriculture",
        },
        {
            "id": "s3",
            "scheme_name": "Rythu Bandhu Scheme",
            "description": "Telangana government's investment support scheme providing Rs.10,000 "
            "per acre per year to farmers for crop investment.",
            "benefits": "Rs.10,000 per acre per year investment support",
            "state_jurisdiction": "Telangana",
            "category": "Investment Support",
            "ministry": "Government of Telangana",
        },
        {
            "id": "s4",
            "scheme_name": "Soil Health Card Scheme",
            "description": "Provides soil health cards to farmers with nutrient recommendations "
            "for their farms to improve productivity.",
            "benefits": "Free soil testing, customized fertilizer recommendations",
            "state_jurisdiction": "Telangana",
            "category": "Soil Health",
            "ministry": "Ministry of Agriculture",
        },
        {
            "id": "s5",
            "scheme_name": "e-NAM (National Agriculture Market)",
            "description": "Pan-India electronic trading portal that networks existing APMC mandis "
            "to create a unified national market for agricultural commodities.",
            "benefits": "Better price discovery, transparent trading, online payment",
            "state_jurisdiction": "Telangana",
            "category": "Market",
            "ministry": "Ministry of Agriculture",
        },
    ]

    # Relational rows first: they never depend on the embedding
    # model, so list/fallback reads work even when vector ingestion
    # fails (e.g. embedding model not yet pulled).
    await _seed_relational_rows(schemes)

    for scheme in schemes:
        await rag_pipeline.ingest_scheme(scheme)

    return len(schemes)
