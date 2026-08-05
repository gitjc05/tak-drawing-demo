import math
import socket
import time
import uuid
from datetime import datetime, timedelta, timezone
from xml.etree import ElementTree as ET


def tak_color(alpha, red, green, blue):
    value = (alpha << 24) + (red << 16) + (green << 8) + blue
    return value - 2**32 if value >= 2**31 else value


# Hardcoded test near the White House.
LAT = 38.8895
LON = -77.0353
BEARING_DEG = 45.0
DEGREES_OF_INACCURACY = 45.0
LINEAR_ERROR_KM = 15.0

HOST = "127.0.0.1"
PORT = 4242
SEND_INTERVAL_SECONDS = 2.0
CALLSIGN = "TAK-BEARING-DEMO"

# TAK colors are signed 32-bit ARGB integers: alpha, red, green, blue.
STROKE_COLOR = tak_color(alpha=255, red=255, green=0, blue=0)  # opaque red
FILL_COLOR = tak_color(alpha=64, red=255, green=0, blue=0)  # transparent red

EARTH_RADIUS_KM = 6371.0088


def cot_time(dt):
    return (
        dt.astimezone(timezone.utc)
        .isoformat(timespec="milliseconds")
        .replace("+00:00", "Z")
    )


def destination_point(lat_deg, lon_deg, bearing_deg, distance_km):
    lat1 = math.radians(lat_deg)
    lon1 = math.radians(lon_deg)
    bearing = math.radians(bearing_deg)
    distance = distance_km / EARTH_RADIUS_KM

    lat2 = math.asin(
        math.sin(lat1) * math.cos(distance)
        + math.cos(lat1) * math.sin(distance) * math.cos(bearing)
    )
    lon2 = lon1 + math.atan2(
        math.sin(bearing) * math.sin(distance) * math.cos(lat1),
        math.cos(distance) - math.sin(lat1) * math.sin(lat2),
    )

    lon2 = (math.degrees(lon2) + 540) % 360 - 180
    return math.degrees(lat2), lon2


def make_triangle_cot(
    lat, lon, bearing_deg, degrees_of_inaccuracy, linear_error_km, uid
):
    left = destination_point(
        lat, lon, bearing_deg - degrees_of_inaccuracy, linear_error_km
    )
    right = destination_point(
        lat, lon, bearing_deg + degrees_of_inaccuracy, linear_error_km
    )
    vertices = [(lat, lon), left, right, (lat, lon)]

    now = datetime.now(timezone.utc)
    event = ET.Element(
        "event",
        {
            "version": "2.0",
            "uid": uid,
            "type": "u-d-f",
            "how": "h-e",
            "time": cot_time(now),
            "start": cot_time(now),
            "stale": cot_time(now + timedelta(seconds=5)),
        },
    )
    ET.SubElement(
        event,
        "point",
        {"lat": f"{lat:.7f}", "lon": f"{lon:.7f}", "hae": "0", "ce": "10", "le": "10"},
    )

    detail = ET.SubElement(event, "detail")
    ET.SubElement(detail, "contact", {"callsign": CALLSIGN})
    ET.SubElement(detail, "strokeColor", {"value": str(STROKE_COLOR)})
    ET.SubElement(detail, "strokeWeight", {"value": "4"})
    ET.SubElement(detail, "fillColor", {"value": str(FILL_COLOR)})

    for point_lat, point_lon in vertices:
        ET.SubElement(detail, "link", {"point": f"{point_lat:.7f},{point_lon:.7f},0"})

    return ET.tostring(event, encoding="utf-8")


def main():
    uid = f"tak-triangle-{uuid.uuid4()}"

    while True:
        cot = make_triangle_cot(
            LAT,
            LON,
            BEARING_DEG,
            DEGREES_OF_INACCURACY,
            LINEAR_ERROR_KM,
            uid,
        )
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.sendto(cot, (HOST, PORT))

        print(f"Sent {len(cot)} bytes to udp://{HOST}:{PORT}")
        time.sleep(SEND_INTERVAL_SECONDS)


if __name__ == "__main__":
    main()
