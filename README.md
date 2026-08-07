# TAK Triangle Drawing Demo

This is a tiny Python demo that sends a transient Cursor on Target (CoT) polygon
to a local WinTAK client. The polygon is a triangle that starts at a known latitude and
longitude, then projects two lines from that point using:

- a bearing in degrees from true north
- an angular uncertainty in degrees
- a linear distance in kilometers

The result is useful for visualizing a simple bearing uncertainty wedge on the
TAK map.

## What It Sends

The script sends one CoT `u-d-p` polygon event to:

```text
udp://127.0.0.1:4242
```

The polygon vertices are encoded as a drawn-shape polyline:

```xml
<detail>
  <shape>
    <polyline closed="true">
      <vertex lat="..." lon="..." />
      <vertex lat="..." lon="..." />
      <vertex lat="..." lon="..." />
    </polyline>
  </shape>
</detail>
```

The polyline is marked `closed="true"` so TAK renders the three vertices as a
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

The script sends one polygon message and exits. WinTAK removes the polygon after
its `stale` time passes, though the WinTAK stale sweeper may take several extra
seconds to remove it from the map and state database.

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

## Expiration

The polygon CoT includes a fixed `stale` timestamp:

```xml
<event uid="TAK-BEARING-DEMO" type="u-d-p" stale="..." />
```

The fixed `DRAWING_UID` is important because repeated demos update the same map
item instead of creating duplicates.

## 3D Display

The polygon vertices intentionally omit height. Using `0` as height means
0 meters height-above-ellipsoid, which can put the shape under the terrain in
WinTAK 3D. The demo also includes best-effort clamp hints in the detail block:

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

The CoT also includes KML-style red and ABGR-style red in the `shape/polyline`
attributes, because WinTAK's shape renderer can prefer one style path over
another. The generic CoT point color uses normal ARGB red, while the polyline
attributes use the integer byte layout that maps to red when parsed as ABGR:

```xml
<polyline color="-16776961" strokeColor="-16776961" fillColor="1073742079" />
<LineStyle>
  <color>ff0000ff</color>
  <width>6</width>
</LineStyle>
<PolyStyle>
  <color>400000ff</color>
</PolyStyle>
```

On WinTAK 4.1, the origin/control point may honor the red color while the
polygon stroke can still render white due to the built-in `u-d-p` style path.

Alpha controls opacity:

- `255` is fully opaque
- `128` is about 50 percent opaque
- `64` is about 25 percent opaque
- `0` is transparent

## Notes

This project is intentionally minimal. It is meant to be easy to revisit later
as a reference for sending simple TAK polygon drawings from Python.
