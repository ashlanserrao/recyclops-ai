"""NAQI calculation (spec V1, V2), including the golden scenarios' AQI values."""

import pytest

from recyclops.domain.aqi import Band, Pollutant, aqi_from, average_24h, band_for, sub_index

PM25, PM10 = Pollutant.PM25, Pollutant.PM10


@pytest.mark.parametrize(("pollutant", "concentration", "expected"), [
    # Every breakpoint lands exactly on its index value.
    (PM25, 0, 0), (PM25, 30, 50), (PM25, 60, 100), (PM25, 90, 200), (PM25, 120, 300), (PM25, 250, 400),
    (PM25, 380, 500), (PM25, 1000, 500),
    (PM10, 50, 50), (PM10, 100, 100), (PM10, 250, 200), (PM10, 350, 300), (PM10, 430, 400), (PM10, 510, 500),
    # A reading in CPCB's published gap (30-31) still gets an index.
    (PM25, 30.5, 51),
    # Halves round up, not to even: 50 + 1.5 * 50/30 = 52.5 -> 53; 100 + 0.75 * 100/150 = 100.5 -> 101.
    (PM25, 31.5, 53), (PM10, 100.75, 101),
])
def test_sub_index(pollutant: Pollutant, concentration: float, expected: int) -> None:
    assert sub_index(pollutant, concentration) == expected


def test_negative_concentration_is_rejected() -> None:
    with pytest.raises(ValueError, match="negative"):
        sub_index(PM25, -1)


@pytest.mark.parametrize(("aqi", "band"), [
    (0, Band.GOOD), (50, Band.GOOD), (51, Band.SATISFACTORY), (100, Band.SATISFACTORY), (101, Band.MODERATE),
    (200, Band.MODERATE), (201, Band.POOR), (300, Band.POOR), (301, Band.VERY_POOR), (400, Band.VERY_POOR),
    (401, Band.SEVERE), (500, Band.SEVERE),
])
def test_band_edges(aqi: int, band: Band) -> None:
    assert band_for(aqi) == band


@pytest.mark.parametrize(("concentrations", "value", "band", "prominent"), [
    ({PM25: 190, PM10: 320}, 354, Band.VERY_POOR, PM25),  # G1 Delhi
    ({PM25: 60, PM10: 190}, 160, Band.MODERATE, PM10),    # G2 Mumbai
    ({PM25: 100}, 233, Band.POOR, PM25),                   # G3 Kolkata
])
def test_golden_scenario_aqi(concentrations: dict[Pollutant, float], value: int, band: Band,
                             prominent: Pollutant) -> None:
    result = aqi_from(concentrations)
    assert (result.value, result.band, result.prominent) == (value, band, prominent)


def test_tie_names_pm25_as_prominent() -> None:
    assert aqi_from({PM10: 100, PM25: 60}).prominent == PM25  # both sub-indices are 100


def test_aqi_needs_a_pollutant() -> None:
    with pytest.raises(ValueError, match="At least one"):
        aqi_from({})


def test_24h_average_needs_16_usable_hours() -> None:
    assert average_24h([100.0] * 15 + [None] * 9) is None
    average = average_24h([100.0] * 15 + [116.0] + [None] * 8)
    assert average is not None
    assert (average.value, average.hours) == (101.0, 16)


def test_24h_average_skips_negative_readings() -> None:
    assert average_24h([50.0] * 15 + [-999.0]) is None
