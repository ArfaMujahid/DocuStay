"""Smarty US Street API – address standardization for property registration."""
from dataclasses import dataclass
from typing import Any
import httpx
from app.config import get_settings


@dataclass
class SmartyAddressResult:
    """Standardized address fields from Smarty US Street API."""
    delivery_line_1: str
    city_name: str
    state_abbreviation: str
    zipcode: str
    plus4_code: str | None
    latitude: float | None
    longitude: float | None


def verify_address(street: str, city: str, state: str, zipcode: str | None = None) -> SmartyAddressResult | None:
    """
    Verify and standardize a US address via Smarty US Street API.
    Returns SmartyAddressResult if a valid match is found, else None.
    Does not raise; returns None on any error or empty response.
    """
    settings = get_settings()
    if not settings.smarty_auth_id or not settings.smarty_auth_token:
        return None

    base_url = "https://us-street.api.smarty.com/street-address"
    params: dict[str, str | int] = {
        "auth-id": settings.smarty_auth_id,
        "auth-token": settings.smarty_auth_token,
        "street": (street or "").strip(),
        "city": (city or "").strip(),
        "state": (state or "").strip(),
        "candidates": 1,
    }
    if zipcode and str(zipcode).strip():
        params["zipcode"] = str(zipcode).strip().split("-")[0][:5]  # 5-digit ZIP only

    try:
        with httpx.Client(timeout=15.0) as client:
            resp = client.get(base_url, params=params)
            if resp.status_code != 200:
                return None
            data = resp.json()
    except Exception:
        return None

    if not isinstance(data, list) or not data:
        return None

    first = data[0]
    if not isinstance(first, dict):
        return None

    delivery_line_1 = first.get("delivery_line_1") or ""
    components = first.get("components") or {}
    metadata = first.get("metadata") or {}

    city_name = components.get("city_name") or ""
    state_abbreviation = components.get("state_abbreviation") or ""
    zipcode_out = components.get("zipcode") or ""
    plus4_code = components.get("plus4_code")

    lat = metadata.get("latitude")
    lon = metadata.get("longitude")
    latitude: float | None = float(lat) if lat is not None and lat != "" else None
    longitude: float | None = float(lon) if lon is not None and lon != "" else None

    return SmartyAddressResult(
        delivery_line_1=str(delivery_line_1).strip(),
        city_name=str(city_name).strip(),
        state_abbreviation=str(state_abbreviation).strip(),
        zipcode=str(zipcode_out).strip(),
        plus4_code=str(plus4_code).strip() if plus4_code else None,
        latitude=latitude,
        longitude=longitude,
    )
