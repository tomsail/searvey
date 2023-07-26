from __future__ import annotations

import datetime
from typing import Any

import numpy as np
import numpy.typing as npt
import pandas as pd
import pytest
import shapely.geometry

from searvey import utils


CET = datetime.timezone(datetime.timedelta(hours=1))


@pytest.mark.parametrize(
    "lon1,expected_lon3",
    [
        (-180, 180),
        (-90, 270),
        (0, 0),
        (90, 90),
        (180, 180),
    ],
)
def test_lon1_to_lon3_scalars(lon1: float, expected_lon3: float) -> None:
    assert utils.lon1_to_lon3(lon1) == expected_lon3


@pytest.mark.parametrize(
    "lon1,expected_lon3",
    [
        (np.array([180]), np.array([180])),
        (np.array([-180, -90, 0, 90, 180]), np.array([180, 270, 0, 90, 180])),
    ],
)
def test_lon1_to_lon3_numpy(lon1: npt.NDArray[Any], expected_lon3: npt.NDArray[Any]) -> None:
    assert np.array_equal(utils.lon1_to_lon3(lon1), expected_lon3)


@pytest.mark.parametrize(
    "lon3,expected_lon1",
    [
        (0, 0),
        (90, 90),
        (180, -180),
        (270, -90),
        (360, 0),
    ],
)
def test_lon3_to_lon1_scalars(lon3: float, expected_lon1: float) -> None:
    assert utils.lon3_to_lon1(lon3) == expected_lon1


@pytest.mark.parametrize(
    "lon3,expected_lon1",
    [
        (np.array([180]), np.array([-180])),
        (np.array([0, 90, 181, 270, 359]), np.array([0, 90, -179, -90, -1])),
    ],
)
def test_lon3_to_lon1_numpy(lon3: float, expected_lon1: float) -> None:
    lon1 = utils.lon3_to_lon1(lon3)
    assert np.array_equal(lon1, expected_lon1)


@pytest.mark.parametrize("lon1", [-162.3, -32.3, -0.02, 0.01, 45.23, 163.2])
def test_lon1_to_lon3_roundtrip(lon1: float) -> None:
    assert lon1 == pytest.approx(utils.lon3_to_lon1(utils.lon1_to_lon3(lon1)))


@pytest.mark.parametrize("lon3", [0.01, 45.23, 163.2, 181.1, 273.2, 332.1])
def test_lon3_to_lon1_roundtrip(lon3: float) -> None:
    assert lon3 == pytest.approx(utils.lon1_to_lon3(utils.lon3_to_lon1(lon3)))


@pytest.mark.parametrize(
    "arg",
    [
        pytest.param("2001-12-28", id="string"),
        pytest.param(pd.Timestamp("2001-12-28"), id="pandas timestamp"),
        pytest.param(datetime.date(2001, 12, 28), id="datetime.date"),
    ],
)
def test_resolve_timestamp_dates(arg) -> None:
    # fmt: off
    assert utils.resolve_timestamp(arg) == pd.Timestamp("2001-12-28 00:00:00+0000", tz="UTC")
    assert utils.resolve_timestamp(arg, timezone_aware=False) == pd.Timestamp("2001-12-28 00:00:00")
    assert utils.resolve_timestamp(arg, timezone="Asia/Tehran") == pd.Timestamp("2001-12-28 00:00:00+0330", tz="Asia/Tehran")
    assert utils.resolve_timestamp(arg, timezone="Asia/Tehran", timezone_aware=False) == pd.Timestamp("2001-12-28 00:00:00")
    # fmt: on


@pytest.mark.parametrize(
    "arg",
    [
        pytest.param("2001-12-28T12:12:12", id="str"),
        pytest.param(pd.Timestamp("2001-12-28T12:12:12"), id="pandas.Timestamp"),
        pytest.param(datetime.datetime(2001, 12, 28, 12, 12, 12), id="datetime.datetime"),
    ],
)
def test_resolve_timestamp_naive_timestamps(arg) -> None:
    # fmt: off
    assert utils.resolve_timestamp(arg) == pd.Timestamp("2001-12-28 12:12:12+0000", tz="UTC")
    assert utils.resolve_timestamp(arg, timezone_aware=False) == pd.Timestamp("2001-12-28 12:12:12")
    assert utils.resolve_timestamp(arg, timezone="Asia/Tehran") == pd.Timestamp("2001-12-28 12:12:12+0330", tz="Asia/Tehran")
    assert utils.resolve_timestamp(arg, timezone="Asia/Tehran", timezone_aware=False) == pd.Timestamp("2001-12-28 12:12:12")
    # fmt: on


@pytest.mark.parametrize(
    "arg",
    [
        # fmt: off
        pytest.param("2001-12-28T12:12:12+0100", id="str"),
        pytest.param(pd.Timestamp("2001-12-28T12:12:12+0100"), id="pandas.Timestamp"),
        pytest.param(datetime.datetime(2001, 12, 28, 12, 12, 12, tzinfo=CET), id="datetime.datetime"),
        # fmt: on
    ],
)
def test_resolve_timestamp_timezone_aware_timestamps(arg) -> None:
    # fmt: off
    assert utils.resolve_timestamp(arg) == pd.Timestamp("2001-12-28 11:12:12+0000", tz="UTC")
    assert utils.resolve_timestamp(arg, timezone_aware=False) == pd.Timestamp("2001-12-28 11:12:12")
    assert utils.resolve_timestamp(arg, timezone="Asia/Tehran") == pd.Timestamp("2001-12-28 14:42:12+0330", tz="Asia/Tehran")
    assert utils.resolve_timestamp(arg, timezone="Asia/Tehran", timezone_aware=False) == pd.Timestamp("2001-12-28 14:42:12")
    # fmt: on


@pytest.mark.parametrize("symmetric", [True, False])
def test_get_region_defaults_return_none(symmetric):
    assert utils.get_region(symmetric=symmetric) is None


def test_get_region_bbox_corners_return_a_polygon():
    lon_min = 1
    lon_max = 2
    lat_min = 1
    lat_max = 2
    region = utils.get_region(
        lon_min=lon_min,
        lon_max=lon_max,
        lat_min=lat_min,
        lat_max=lat_max,
    )
    assert isinstance(region, shapely.geometry.Polygon)
    assert region == shapely.geometry.box(lon_min, lat_min, lon_max, lat_max)


def test_get_region_raises_when_both_region_and_bbox_are_specified():
    with pytest.raises(ValueError) as exc:
        utils.get_region(
            region=shapely.geometry.box(0, 0, 1, 1),
            lon_min=1,
        )
    assert str(exc.value) == "You must specify either `region` or the `BBox` corners, not both"


def test_get_region_symmetric_raises_for_longitude_over_180():
    with pytest.raises(ValueError) as exc:
        utils.get_region(lon_max=300, symmetric=True)
    assert "less than or equal to 180" in str(exc.value)


def test_get_region_asymmetric_raises_for_longitude_less_than_0():
    with pytest.raises(ValueError) as exc:
        utils.get_region(lon_min=-100, symmetric=False)
    assert "greater than or equal to 0" in str(exc.value)
