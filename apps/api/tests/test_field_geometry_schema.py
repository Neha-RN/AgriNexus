from decimal import Decimal
from types import SimpleNamespace

from geoalchemy2.shape import from_shape
from shapely.geometry import MultiPolygon, Polygon

from app.schemas.field import FieldRead


def _sample_multipolygon_wkb():
    polygon = Polygon([(0, 0), (0, 1), (1, 1), (1, 0), (0, 0)])
    multipolygon = MultiPolygon([polygon])
    return from_shape(multipolygon, srid=4326)


def test_field_read_converts_geometry_to_geojson() -> None:
    fake_field = SimpleNamespace(
        id=1,
        country_id=1,
        name="Test Field",
        crop_type="Wheat",
        area_hectares=Decimal("12.5"),
        geometry=_sample_multipolygon_wkb(),
    )

    result = FieldRead.model_validate(fake_field)

    assert result.geometry is not None
    assert result.geometry["type"] == "MultiPolygon"
    assert result.geometry["coordinates"][0][0][0] == (0.0, 0.0)


def test_field_read_preserves_existing_fields() -> None:
    fake_field = SimpleNamespace(
        id=1,
        country_id=2,
        name="Test Field",
        crop_type="Wheat",
        area_hectares=Decimal("12.5"),
        geometry=_sample_multipolygon_wkb(),
    )

    result = FieldRead.model_validate(fake_field)

    assert result.id == 1
    assert result.country_id == 2
    assert result.name == "Test Field"
    assert result.crop_type == "Wheat"
    assert result.area_hectares == Decimal("12.5")


def test_field_read_geometry_none() -> None:
    fake_field = SimpleNamespace(
        id=2,
        country_id=1,
        name="No Geometry Field",
        crop_type=None,
        area_hectares=None,
        geometry=None,
    )

    result = FieldRead.model_validate(fake_field)
    assert result.geometry is None