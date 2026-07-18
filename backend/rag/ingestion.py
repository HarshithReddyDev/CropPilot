import json

from rag.pipeline import rag_pipeline


async def ingest_schemes_from_json(filepath: str):
    with open(filepath) as f:
        schemes = json.load(f)

    for scheme in schemes:
        await rag_pipeline.ingest_scheme(scheme)

    return len(schemes)


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

    for scheme in schemes:
        await rag_pipeline.ingest_scheme(scheme)

    return len(schemes)
