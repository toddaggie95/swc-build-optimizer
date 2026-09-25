"""Strict import/export for the historical Designer code grammar."""

import re
from urllib.parse import parse_qs, urlencode, urlsplit

from .models import Catalog, City, Placement


def parse_url(url: str, catalog: Catalog, *, name: str = "Imported city") -> City:
    parsed = urlsplit(url)
    if (
        parsed.scheme != "https"
        or parsed.netloc != "www.swcombine.com"
        or parsed.path not in ("/citydesigner/", "/citydesigner/index.php")
    ):
        raise ValueError("Expected an HTTPS SWC City Designer URL")
    values = parse_qs(parsed.query, keep_blank_values=True).get("code", [])
    if len(values) != 1:
        raise ValueError("Expected exactly one code parameter")
    code = values[0]
    layout, marker, suffix = code.partition("|")
    state = marker + suffix
    rows = layout.split(";")
    if rows[-1] == "":
        rows.pop()
    if layout == "":
        rows = []
    placements = []
    known = catalog.by_id()
    for i, row in enumerate(rows):
        if not re.fullmatch(r"[1-9][0-9]*,-?[0-9]+,-?[0-9]+,[vh]", row):
            raise ValueError(f"Malformed placement {i + 1}: {row!r}")
        fid, x, y, orientation = row.split(",")
        if int(fid) not in known:
            raise ValueError(f"Unknown facility type {fid}; extend the catalog explicitly")
        placements.append(
            Placement(
                id=f"p{i + 1:02d}",
                facility_id=int(fid),
                x=int(x),
                y=int(y),
                orientation=orientation,
            )
        )
    return City(name=name, placements=tuple(placements), designer_state=state, source_url=url)


def to_url(city: City) -> str:
    if (city.width, city.height) != (20, 20):
        raise ValueError("Designer export supports only the 20x20 placement grid")
    code = "".join(f"{p.facility_id},{p.x},{p.y},{p.orientation};" for p in city.placements)
    return "https://www.swcombine.com/citydesigner/index.php?" + urlencode(
        {"code": code + city.designer_state}
    )
