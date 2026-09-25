"""Pure cell geometry. A border is never a free side."""

from .models import City, FacilityType, Placement

Cell = tuple[int, int]


def dimensions(p: Placement, facility: FacilityType) -> tuple[int, int]:
    if p.orientation == "v":
        return facility.width, facility.height
    return facility.height, facility.width


def cells(p: Placement, facility: FacilityType) -> frozenset[Cell]:
    w, h = dimensions(p, facility)
    return frozenset((x, y) for x in range(p.x, p.x + w) for y in range(p.y, p.y + h))


def in_bounds(cell: Cell, city: City) -> bool:
    x, y = cell
    return 0 <= x < city.width and 0 <= y < city.height


def side_strips(p: Placement, facility: FacilityType) -> dict[str, tuple[Cell, ...]]:
    w, h = dimensions(p, facility)
    return {
        "north": tuple((x, p.y - 1) for x in range(p.x, p.x + w)),
        "south": tuple((x, p.y + h) for x in range(p.x, p.x + w)),
        "east": tuple((p.x + w, y) for y in range(p.y, p.y + h)),
        "west": tuple((p.x - 1, y) for y in range(p.y, p.y + h)),
    }


def free_sides(
    p: Placement, facility: FacilityType, city: City, occupied: set[Cell]
) -> tuple[str, ...]:
    # ALL cells in the full adjacent strip must be in the city and unoccupied.
    # Do not clip strips to the grid: all([]) would incorrectly make borders roads.
    return tuple(
        name
        for name, strip in side_strips(p, facility).items()
        if all(in_bounds(c, city) and c not in occupied for c in strip)
    )
