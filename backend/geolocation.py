import json
import socket
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen


def lookup_ip(ip_address):
    if not ip_address or ip_address in {"Unknown", "Unavailable"}:
        return {"town": "Unavailable", "country": "Unavailable", "state": "Unavailable", "source": "Unavailable"}

    try:
        socket.inet_aton(ip_address)
    except OSError:
        return {"town": "Unavailable", "country": "Unavailable", "state": "Unavailable", "source": "Unavailable"}

    request = Request(
        f"https://ipwho.is/{quote(ip_address)}",
        headers={"User-Agent": "ByteNest admin dashboard"},
    )
    try:
        with urlopen(request, timeout=3) as response:
            data = json.load(response)
    except Exception:
        return {"town": "Unavailable", "country": "Unavailable", "state": "Unavailable", "source": "IP estimate"}

    if not data.get("success", False):
        return {"town": "Unavailable", "country": "Unavailable", "state": "Unavailable", "source": "IP estimate"}

    return {
        "town": data.get("city") or "Unavailable",
        "country": data.get("country") or "Unavailable",
        "state": data.get("region") or "Unavailable",
        "source": "IP estimate",
    }


def lookup_coordinates(latitude, longitude):
    try:
        latitude = float(latitude)
        longitude = float(longitude)
        if not -90 <= latitude <= 90 or not -180 <= longitude <= 180:
            raise ValueError
    except (TypeError, ValueError):
        return {}

    query = urlencode({"lat": latitude, "lon": longitude, "format": "jsonv2"})
    request = Request(
        f"https://nominatim.openstreetmap.org/reverse?{query}",
        headers={"User-Agent": "ByteNest location lookup contact@example.com"},
    )
    try:
        with urlopen(request, timeout=4) as response:
            address = json.load(response).get("address", {})
    except Exception:
        return {}

    return {
        "town": address.get("town") or address.get("city") or address.get("village") or "Unavailable",
        "country": address.get("country") or "Unavailable",
        "state": address.get("state") or "Unavailable",
        "source": "Browser location",
    }


def resolve_location(location, ip_address):
    if isinstance(location, dict):
        try:
            latitude = float(location.get("latitude"))
            longitude = float(location.get("longitude"))
            if -90 <= latitude <= 90 and -180 <= longitude <= 180:
                precise_location = lookup_coordinates(latitude, longitude)
                if precise_location:
                    return precise_location
                return {
                    "town": "Unavailable",
                    "country": "Unavailable",
                    "state": "Unavailable",
                    "source": "Browser coordinates",
                }
        except (TypeError, ValueError):
            pass
    fallback = lookup_ip(ip_address)
    fallback["source"] = "IP estimate" if fallback["source"] != "Unavailable" else "Unavailable"
    return fallback