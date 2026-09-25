import pytest

from swc_build_optimizer.geometry import cells, free_sides
from swc_build_optimizer.models import City, Placement
from swc_build_optimizer.placements import legal_additions
from swc_build_optimizer.validation import validate


def p(name, x, y, fid=1, orientation="v"):
    return Placement(id=name, facility_id=fid, x=x, y=y, orientation=orientation)


def test_border_is_not_road(catalog):
    corner = p("corner", 0, 0)
    city = City(name="corner", width=3, height=3, placements=(corner,))
    assert free_sides(corner, catalog.by_id()[1], city, {(0, 0)}) == ("south", "east")
    # Once the southern neighbor is occupied, the corner has only ONE road side.
    city = city.model_copy(update={"placements": (corner, p("block", 0, 1))})
    result = validate(city, catalog)
    assert [(i.code, i.placement_ids) for i in result.issues] == [
        ("insufficient_access", ("corner",))
    ]


def test_single_cell_city_has_no_roads(catalog):
    assert not validate(
        City(name="tiny", width=1, height=1, placements=(p("a", 0, 0),)), catalog
    ).geometry_valid


def test_complete_strip_not_just_one_neighbor(catalog):
    building = p("office", 2, 1, fid=2)
    city = City(name="strips", width=5, height=5)
    assert "west" not in free_sides(building, catalog.by_id()[2], city, {(1, 2)})
    assert "east" in free_sides(building, catalog.by_id()[2], city, {(1, 2)})


def test_rotation_and_complete_bounds(catalog):
    office = catalog.by_id()[2]
    assert cells(p("a", 1, 2, 2, "h"), office) == {(1, 2), (2, 2), (3, 2)}
    assert cells(p("a", 1, 2, 2, "v"), office) == {(1, 2), (1, 3), (1, 4)}
    result = validate(City(name="outside", placements=(p("a", 19, 0, 2, "h"),)), catalog)
    assert result.issues[0].code == "out_of_bounds"
    assert "two_free_sides" not in result.checked


@pytest.mark.parametrize("x,y", [(-1, 0), (0, -1), (20, 0), (0, 20)])
def test_invalid_anchors(catalog, x, y):
    assert (
        validate(City(name="bounds", placements=(p("a", x, y),)), catalog).issues[0].code
        == "out_of_bounds"
    )


def test_overlap_and_unknown_type(catalog):
    result = validate(City(name="overlap", placements=(p("a", 1, 1), p("b", 1, 1))), catalog)
    assert result.issues[0].code == "overlap"
    assert (
        validate(City(name="unknown", placements=(p("a", 0, 0, 999),)), catalog).issues[0].code
        == "unknown_facility"
    )


def test_addition_must_preserve_existing_access(catalog):
    city = City(name="baseline", width=3, height=3, placements=(p("corner", 0, 0),))
    assert validate(city, catalog).geometry_valid
    # The candidate at (0,1) has two clear sides itself, but strands the corner.
    candidate = p("candidate", 0, 1)
    assert len(free_sides(candidate, catalog.by_id()[1], city, {(0, 0), (0, 1)})) == 2
    additions = legal_additions(city, catalog, 1)
    assert (0, 1) not in {(a.x, a.y) for a in additions}
    assert (2, 2) in {(a.x, a.y) for a in additions}
    assert all(not a.fixed for a in additions)
    assert city.placements == (p("corner", 0, 0),)


def test_enumeration_is_stable_and_deduplicates_square_rotations(catalog):
    city = City(name="empty", width=3, height=3)
    additions = legal_additions(city, catalog, 1)
    assert len(additions) == 9
    assert additions == legal_additions(city, catalog, 1)
    assert all(p.orientation == "v" for p in additions)
    assert [(p.x, p.y) for p in additions] == [(x, y) for y in range(3) for x in range(3)]


def test_non_square_enumeration_has_both_orientations(catalog):
    additions = legal_additions(City(name="empty", width=5, height=5), catalog, 2)
    assert {p.orientation for p in additions} == {"v", "h"}


def test_reject_invalid_baseline_and_unknown_probe(catalog):
    with pytest.raises(ValueError, match="baseline"):
        legal_additions(City(name="bad", placements=(p("bad", -1, 0),)), catalog, 1)
    with pytest.raises(ValueError, match="Unknown"):
        legal_additions(City(name="empty"), catalog, 999)


def test_candidate_id_does_not_collide(catalog):
    city = City(name="IDs", placements=(p("addition", 0, 0),))
    assert all(a.id == "addition_" for a in legal_additions(city, catalog, 1))
