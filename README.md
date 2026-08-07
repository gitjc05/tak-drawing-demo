# TAK Triangle Drawing Demo

This is a tiny Python demo that sends a Cursor on Target (CoT) polygon to a local
WinTAK client. The polygon is a triangle that starts at a known latitude and
longitude, then projects two lines from that point using:

- a bearing in degrees from true north
- an angular uncertainty in degrees
- a linear distance in kilometers

The result is useful for visualizing a simple bearing uncertainty wedge on the
TAK map.

## What It Sends

The script sends a CoT `u-d-f` freehand drawing event to:

```text
udp://127.0.0.1:4242
```

The polygon vertices are encoded as direct CoT detail links:

```xml
<detail>
  <link point="lat,lon,hae" />
  <link point="lat,lon,hae" />
  <link point="lat,lon,hae" />
  <link point="lat,lon,hae" />
</detail>
```

The first point is repeated as the final point so TAK renders the shape as a
closed polygon.

## Requirements

- Python 3
- WinTAK running locally
- WinTAK configured to listen for CoT on UDP port `4242`

No Python packages are required.

## Run

```powershell
python tak_triangle_demo.py
```

The script sends the polygon for `STALE_SECONDS`, then sends an empty drawing
update for the same drawing UID. This is intentional: WinTAK can treat freehand
drawings differently from normal map markers, so a separate delete event may
appear as its own marker instead of removing the drawing.

Use `Ctrl+C` to stop it from a terminal. On normal interruption, the script still
tries to send the empty drawing update before exiting.

## Change The Test Values

Edit the constants near the top of `tak_triangle_demo.py`:

```python
LAT = 38.8895
LON = -77.0353
BEARING_DEG = 45.0
DEGREES_OF_INACCURACY = 45.0
LINEAR_ERROR_KM = 15.0
STALE_SECONDS = 10.0
```

By default, the origin is near the White House.

## Expiration And Removal

The drawing CoT includes a normal `stale` timestamp. When that time is reached,
the script sends another `u-d-f` event with the exact same UID, but no polygon
vertex links:

```xml
<event uid="TAK-BEARING-DEMO-TRIANGLE" type="u-d-f" ...>
  <point lat="38.8895000" lon="-77.0353000" hae="0" ce="10" le="10" />
  <detail>
    <contact callsign="TAK-BEARING-DEMO" />
    <strokeColor value="0" />
    <strokeWeight value="0" />
    <fillColor value="0" />
  </detail>
</event>
```

The fixed `DRAWING_UID` is important. If every run generated a random UID, later
runs could not target old drawings for removal.

## 3D Display

The polygon vertex links intentionally use `lat,lon` instead of `lat,lon,0`.
Using `0` as the height means 0 meters height-above-ellipsoid, which can put the
shape under the terrain in WinTAK 3D. The demo also includes best-effort clamp
hints in the detail block:

```xml
<altitudeMode>clampToGround</altitudeMode>
<heightStyle value="clampToGround" />
```

## Colors

TAK colors are signed 32-bit ARGB integers:

```text
alpha, red, green, blue
```

This demo includes a helper so you can use normal channel values from `0` to
`255`:

```python
STROKE_COLOR = tak_color(alpha=255, red=255, green=0, blue=0)
FILL_COLOR = tak_color(alpha=64, red=255, green=0, blue=0)
```

Alpha controls opacity:

- `255` is fully opaque
- `128` is about 50 percent opaque
- `64` is about 25 percent opaque
- `0` is transparent

## Notes

This project is intentionally minimal. It is meant to be easy to revisit later
as a reference for sending simple TAK polygon drawings from Python.
