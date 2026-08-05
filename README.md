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

The script sends the same polygon every two seconds until the program is closed.
Use `Ctrl+C` to stop it from a terminal.

## Change The Test Values

Edit the constants near the top of `tak_triangle_demo.py`:

```python
LAT = 38.8895
LON = -77.0353
BEARING_DEG = 45.0
DEGREES_OF_INACCURACY = 45.0
LINEAR_ERROR_KM = 15.0
```

By default, the origin is near the White House.

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
