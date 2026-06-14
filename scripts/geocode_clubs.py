#!/usr/bin/env python3
"""Build data/club_geocodes.json with per-club coordinates.

Sources, in order of preference:
1. City of Toronto CSV: exact lat/lng embedded in the facility-map URLs.
2. OTA CSV: street addresses from the Google Maps links, geocoded via
   Nominatim (OpenStreetMap) at 1 request/second with a postal-code fallback.

The output is a cache keyed by normalized club name; reruns skip clubs that
are already resolved, so the script is resumable and cheap to re-execute.
"""

from __future__ import annotations

import csv
import json
import re
import ssl
import time
import urllib.parse
import urllib.request
from pathlib import Path

try:
    import certifi

    SSL_CONTEXT = ssl.create_default_context(cafile=certifi.where())
except ImportError:
    SSL_CONTEXT = ssl.create_default_context()

BASE_DIR = Path(__file__).resolve().parents[1]
OTA_CSV = BASE_DIR / "Tennis clubs data - OTA.csv"
TORONTO_CSV = BASE_DIR / "Tennis clubs data - CityofToronto.csv"
OUTPUT = BASE_DIR / "data" / "club_geocodes.json"

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
USER_AGENT = "GTA-tennis-clubs-waitlist/1.0 (github.com/YFC-ophey/GTA-tennis-clubs-waitlist)"

# Sanity bounds: southern Ontario incl. Ottawa/Kingston/London
LAT_RANGE = (41.5, 46.5)
LNG_RANGE = (-84.0, -74.0)

POSTAL_RE = re.compile(r"\b([A-Za-z]\d[A-Za-z])\s*(\d[A-Za-z]\d)\b")


def normalize_name(name: str) -> str:
    return re.sub(r"\s+", " ", str(name or "").strip()).lower()


def in_bounds(lat: float, lng: float) -> bool:
    return LAT_RANGE[0] <= lat <= LAT_RANGE[1] and LNG_RANGE[0] <= lng <= LNG_RANGE[1]


def load_existing() -> dict:
    if OUTPUT.exists():
        try:
            return json.loads(OUTPUT.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            return {}
    return {}


def toronto_coords() -> dict:
    """Exact coordinates parsed out of the toronto.ca facility-map URLs.

    The CSV header has several blank column names, so a DictReader collapses
    them and loses the URL that carries the coordinates; read positionally
    instead. Columns: location(0), name(1), then the facility-map URL with
    lat/lng appears among the later cells.
    """
    results = {}
    if not TORONTO_CSV.exists():
        return results
    with TORONTO_CSV.open(encoding="utf-8-sig") as handle:
        rows = list(csv.reader(handle))
    for cells in rows[1:]:
        if len(cells) < 2:
            continue
        location, name = cells[0], cells[1]
        blob = " ".join(str(c) for c in cells if c)
        match = re.search(r"lat=([0-9.\-]+)&lng=([0-9.\-]+)", blob)
        if not name or not match:
            continue
        lat, lng = float(match.group(1)), float(match.group(2))
        if in_bounds(lat, lng):
            results[normalize_name(name)] = {
                "name": name,
                "lat": round(lat, 6),
                "lng": round(lng, 6),
                "source": "toronto_csv",
                "address": location,
            }
    return results


def ota_addresses() -> dict:
    """Club name -> street address from the OTA Google Maps links."""
    addresses = {}
    if not OTA_CSV.exists():
        return addresses
    with OTA_CSV.open(encoding="utf-8-sig") as handle:
        for row in csv.DictReader(handle):
            name = row.get("name", "")
            link = row.get("google map", "")
            if not name or "maps.google" not in str(link):
                continue
            query = urllib.parse.parse_qs(urllib.parse.urlparse(link).query).get("q")
            if query and query[0].strip():
                addresses[normalize_name(name)] = {"name": name, "address": query[0].strip()}
    return addresses


def nominatim_lookup(query: str) -> tuple[float, float] | None:
    params = urllib.parse.urlencode(
        {"q": query, "format": "json", "limit": 1, "countrycodes": "ca"}
    )
    request = urllib.request.Request(
        f"{NOMINATIM_URL}?{params}", headers={"User-Agent": USER_AGENT}
    )
    try:
        with urllib.request.urlopen(request, timeout=15, context=SSL_CONTEXT) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except Exception:  # noqa: BLE001
        return None
    if not payload:
        return None
    lat, lng = float(payload[0]["lat"]), float(payload[0]["lon"])
    return (lat, lng) if in_bounds(lat, lng) else None


def main() -> None:
    geocodes = load_existing()
    fresh_toronto = 0
    for key, entry in toronto_coords().items():
        if key not in geocodes:
            geocodes[key] = entry
            fresh_toronto += 1

    pending = {
        key: info
        for key, info in ota_addresses().items()
        if key not in geocodes
    }
    print(f"Toronto CSV exact coords added: {fresh_toronto}")
    print(f"OTA addresses to geocode: {len(pending)}")

    resolved = failed = 0
    for index, (key, info) in enumerate(sorted(pending.items()), start=1):
        address = info["address"]
        coords = nominatim_lookup(address)
        source = "nominatim_address"
        if coords is None:
            postal = POSTAL_RE.search(address)
            if postal:
                time.sleep(1.1)
                coords = nominatim_lookup(f"{postal.group(1)} {postal.group(2)}, Canada")
                source = "nominatim_postal"
        if coords is not None:
            geocodes[key] = {
                "name": info["name"],
                "lat": round(coords[0], 6),
                "lng": round(coords[1], 6),
                "source": source,
                "address": address,
            }
            resolved += 1
        else:
            failed += 1
            print(f"  no match: {info['name']} ({address})")
        if index % 25 == 0:
            OUTPUT.write_text(
                json.dumps(geocodes, indent=1, ensure_ascii=False, sort_keys=True),
                encoding="utf-8",
            )
            print(f"  progress: {index}/{len(pending)} (resolved {resolved}, failed {failed})")
        time.sleep(1.1)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        json.dumps(geocodes, indent=1, ensure_ascii=False, sort_keys=True), encoding="utf-8"
    )
    print(f"Done. Total cached: {len(geocodes)} (new resolved {resolved}, failed {failed})")
    print(f"Wrote {OUTPUT}")


if __name__ == "__main__":
    main()
