import math
import socket
from datetime import datetime, timedelta, timezone
from xml.etree import ElementTree as ET


def tak_color(alpha, red, green, blue):
    value = (alpha << 24) + (red << 16) + (green << 8) + blue
    return value - 2**32 if value >= 2**31 else value


def kml_color(alpha, red, green, blue):
    return f"{alpha:02x}{blue:02x}{green:02x}{red:02x}"


def html_color(red, green, blue):
    return f"#{red:02x}{green:02x}{blue:02x}"


# Hardcoded test near the White House.
LAT = 38.8895
LON = -77.0353
BEARING_DEG = 45.0
DEGREES_OF_INACCURACY = 45.0
LINEAR_ERROR_KM = 15.0

HOST = "127.0.0.1"
PORT = 4242
STALE_SECONDS = 10.0
CALLSIGN = "TAK-BEARING-DEMO"
DRAWING_UID = "TAK-BEARING-DEMO"
DRAWING_TYPE = "u-d-p"

# TAK colors are signed 32-bit ARGB integers: alpha, red, green, blue.
STROKE_COLOR = tak_color(alpha=255, red=255, green=0, blue=0)  # opaque red
FILL_COLOR = tak_color(alpha=64, red=255, green=0, blue=0)  # transparent red
STROKE_ABGR_COLOR = tak_color(alpha=255, red=0, green=0, blue=255)  # opaque red if parsed as ABGR
FILL_ABGR_COLOR = tak_color(alpha=64, red=0, green=0, blue=255)  # transparent red if parsed as ABGR
STROKE_KML_COLOR = kml_color(alpha=255, red=255, green=0, blue=0)  # opaque red
FILL_KML_COLOR = kml_color(alpha=64, red=255, green=0, blue=0)  # transparent red
STROKE_HTML_COLOR = html_color(red=255, green=0, blue=0)  # opaque red

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


def send_cot(cot):
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.sendto(cot, (HOST, PORT))


def triangle_vertices(lat, lon, bearing_deg, degrees_of_inaccuracy, linear_error_km):
    left = destination_point(
        lat, lon, bearing_deg - degrees_of_inaccuracy, linear_error_km
    )
    right = destination_point(
        lat, lon, bearing_deg + degrees_of_inaccuracy, linear_error_km
    )
    return [(lat, lon), left, right]


def make_triangle_cot(lat, lon, bearing_deg, degrees_of_inaccuracy, linear_error_km, uid, stale_at):
    vertices = triangle_vertices(
        lat, lon, bearing_deg, degrees_of_inaccuracy, linear_error_km
    )

    now = datetime.now(timezone.utc)
    event = ET.Element(
        "event",
        {
            "version": "2.0",
            "uid": uid,
            "type": DRAWING_TYPE,
            "how": "h-e",
            "time": cot_time(now),
            "start": cot_time(now),
            "stale": cot_time(stale_at),
        },
    )
    ET.SubElement(
        event,
        "point",
        {
            "lat": f"{lat:.7f}",
            "lon": f"{lon:.7f}",
            "hae": "0",
            "ce": "10",
            "le": "10",
        },
    )

    detail = ET.SubElement(event, "detail")
    ET.SubElement(detail, "contact", {"callsign": CALLSIGN})
    ET.SubElement(detail, "color", {"argb": str(STROKE_COLOR), "value": str(STROKE_COLOR)})
    ET.SubElement(detail, "strokeColor", {"value": str(STROKE_COLOR)})
    ET.SubElement(detail, "strokeWeight", {"value": "6"})
    ET.SubElement(detail, "strokeStyle", {"value": "solid"})
    ET.SubElement(detail, "fillColor", {"value": str(FILL_COLOR)})
    ET.SubElement(detail, "__shapeExtras", {"cpvis": "false", "editable": "false"})
    ET.SubElement(detail, "tog", {"enabled": "0"})
    ET.SubElement(detail, "labels_on", {"value": "false"})
    ET.SubElement(detail, "altitudeMode").text = "clampToGround"
    ET.SubElement(detail, "heightStyle", {"value": "clampToGround"})

    shape = ET.SubElement(detail, "shape")
    polyline = ET.SubElement(
        shape,
        "polyline",
        {
            "closed": "true",
            "color": str(STROKE_ABGR_COLOR),
            "strokeColor": str(STROKE_ABGR_COLOR),
            "strokeWeight": "6",
            "fillColor": str(FILL_ABGR_COLOR),
        },
    )
    for point_lat, point_lon in vertices:
        ET.SubElement(
            polyline,
            "vertex",
            {"lat": f"{point_lat:.7f}", "lon": f"{point_lon:.7f}"},
        )

    add_style_link(detail, uid)
    add_style_link(shape, uid)

    return ET.tostring(event, encoding="utf-8")


def add_style_link(parent, uid):
    style_link = ET.SubElement(
        parent,
        "link",
        {"uid": f"{uid}.Style", "type": "b-x-KmlStyle", "relation": "p-c"},
    )
    style = ET.SubElement(style_link, "Style")

    line_style = ET.SubElement(style, "LineStyle")
    ET.SubElement(line_style, "color").text = STROKE_KML_COLOR
    ET.SubElement(line_style, "width").text = "6"

    poly_style = ET.SubElement(style, "PolyStyle")
    ET.SubElement(poly_style, "color").text = FILL_KML_COLOR

    vector_style = ET.SubElement(style, "VectorShapeStyle", {"name": "Red"})
    ET.SubElement(
        vector_style,
        "Stroke",
        {"color": STROKE_HTML_COLOR, "opacity": "255", "width": "6", "pattern": "FFFF"},
    )
    ET.SubElement(
        vector_style,
        "Fill",
        {"color": STROKE_HTML_COLOR, "opacity": "64"},
    )

def main():
    uid = DRAWING_UID
    stale_at = datetime.now(timezone.utc) + timedelta(seconds=STALE_SECONDS)

    cot = make_triangle_cot(
        LAT,
        LON,
        BEARING_DEG,
        DEGREES_OF_INACCURACY,
        LINEAR_ERROR_KM,
        uid,
        stale_at,
    )
    send_cot(cot)
    print(f"Sent 1 transient red polygon. Stale time is {cot_time(stale_at)}")


if __name__ == "__main__":
    main()
