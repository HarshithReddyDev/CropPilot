"""Normalization and data-quality layer for OGD mandi observations.

Parsing uses `Decimal` for prices. Malformed records are rejected with a
reason instead of being coerced into fake values. Observations are never
merged across variety, grade, unit, market, or district here.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

SOURCE_NAME = "AGMARKNET"

_WHITESPACE_RE = re.compile(r"\s+")

# Accepted unit spellings (case-insensitive) all meaning rupees per quintal.
_QUINTAL_UNITS = {
    "inr/quintal",
    "rs/quintal",
    "rs./quintal",
    "rupees/quintal",
    "quintal",
    "qtl",
}
CANONICAL_UNIT = "INR/quintal"

_DATE_FORMATS = ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d")


@dataclass(frozen=True)
class NormalizedObservation:
    state: str
    district: str
    market: str
    commodity: str
    variety: str
    grade: str
    min_price: Decimal
    max_price: Decimal
    modal_price: Decimal
    price_per_unit: str
    arrival_date: date
    source: str = SOURCE_NAME
    # Arrivals ride along with the observation grain but never enter the
    # natural key and are never treated as prices.
    arrivals: Decimal | None = None
    arrival_unit: str | None = None

    def natural_key(self) -> tuple[str, str, str, str, str, str, str]:
        return (
            self.state,
            self.district,
            self.market,
            self.commodity,
            self.variety,
            self.grade,
            self.arrival_date.isoformat(),
        )


def normalize_text(value: object) -> str:
    """Strip and collapse whitespace. Empty/None becomes ""."""
    if value is None:
        return ""
    text = _WHITESPACE_RE.sub(" ", str(value)).strip()
    return text


def parse_price(value: object) -> Decimal | None:
    """Parse a price string/number. Returns None for malformed values."""
    if value is None:
        return None
    text = str(value).strip().replace(",", "")
    if not text or text.lower() in {"na", "n/a", "null", "none", "-"}:
        return None
    try:
        amount = Decimal(text)
    except InvalidOperation:
        return None
    if amount.is_nan() or amount.is_infinite() or amount < 0:
        return None
    return amount


def parse_arrival_date(value: object) -> date | None:
    """Parse Arrival_Date. Returns None when the value is missing or malformed."""
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    # OGD sometimes ships ISO datetimes; accept the date prefix.
    if "T" in text:
        text = text.split("T", 1)[0]
    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    return None


def normalize_unit(value: object) -> str | None:
    """Map accepted rupees-per-quintal spellings to INR/quintal.

    Returns None for missing or incompatible units so the caller can
    quarantine the record instead of mixing incompatible units.
    """
    text = normalize_text(value).lower().replace(" ", "")
    if not text:
        return None
    if text in _QUINTAL_UNITS:
        return CANONICAL_UNIT
    return None


def normalize_record(raw: dict) -> tuple[NormalizedObservation | None, str | None]:
    """Normalize one raw OGD record.

    Returns (observation, None) on success or (None, reason) on rejection.
    The raw payload is kept by the caller for provenance.
    """
    state = normalize_text(raw.get("state"))
    district = normalize_text(raw.get("district"))
    market = normalize_text(raw.get("market"))
    commodity = normalize_text(raw.get("commodity"))
    variety = normalize_text(raw.get("variety"))
    grade = normalize_text(raw.get("grade"))

    if not state or not market or not commodity:
        return None, "missing required dimension (state/market/commodity)"

    arrival = parse_arrival_date(raw.get("arrival_date"))
    if arrival is None:
        return None, "missing or malformed arrival_date"
    # Observation dates come from the source and can never be in the
    # future; a later date is a source typo, not tomorrow's price.
    if arrival > date.today():
        return None, "arrival_date is in the future"

    min_price = parse_price(raw.get("min_price"))
    max_price = parse_price(raw.get("max_price"))
    modal_price = parse_price(raw.get("modal_price"))
    if min_price is None or max_price is None or modal_price is None:
        return None, "missing or malformed price"

    if not (min_price <= modal_price <= max_price):
        return None, "price ordering violated (min<=modal<=max)"

    unit = normalize_unit(raw.get("unit", "Rs/Quintal"))
    # OGD mandi records are quoted in rupees per quintal; when the source
    # omits the unit, treat it as the documented default rather than
    # rejecting years of valid observations.
    if unit is None:
        if normalize_text(raw.get("unit")) == "":
            unit = CANONICAL_UNIT
        else:
            return None, "incompatible or unknown unit"

    # Arrivals are informational quantity metadata. Malformed arrival
    # quantities quarantine only the arrivals fields, never the prices:
    # a bad arrivals value stores as NULL, never as zero.
    arrivals = parse_price(raw.get("arrivals"))
    if raw.get("arrivals") is None or normalize_text(raw.get("arrivals")) == "":
        arrivals = None
    arrival_unit = normalize_text(raw.get("unitOfArrivals")) or None

    return (
        NormalizedObservation(
            state=state,
            district=district,
            market=market,
            commodity=commodity,
            variety=variety,
            grade=grade,
            min_price=min_price,
            max_price=max_price,
            modal_price=modal_price,
            price_per_unit=unit,
            arrival_date=arrival,
            arrivals=arrivals,
            arrival_unit=arrival_unit,
        ),
        None,
    )
