import json
import socket
from urllib.parse import quote
from urllib.request import Request, urlopen


def lookup_ip(ip_address):
    if not ip_address or ip_address in {"Unknown", "Unavailable"}:
        return {"country": "Unavailable", "state": "Unavailable"}

    try:
        socket.inet_aton(ip_address)
    except OSError:
        return {"country": "Unavailable", "state": "Unavailable"}

    request = Request(
        f"https://ipwho.is/{quote(ip_address)}",
        headers={"User-Agent": "ByteNest admin dashboard"},
    )
    try:
        with urlopen(request, timeout=3) as response:
            data = json.load(response)
    except Exception:
        return {"country": "Unavailable", "state": "Unavailable"}

    if not data.get("success", False):
        return {"country": "Unavailable", "state": "Unavailable"}

    return {
        "country": data.get("country") or "Unavailable",
        "state": data.get("region") or "Unavailable",
    }