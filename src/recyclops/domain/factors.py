"""Every published figure the impact numbers rest on, with its source. Nothing here is estimated by the AI.

Where a figure is an assumption rather than a measurement, it says so; the README repeats these.
"""

from dataclasses import dataclass

from recyclops.domain.household import CommuteMode, Intensity

IGHGP_ROAD = "India GHG Program (WRI India, TERI, CII), India Specific Road Transport Emission Factors, v1.0, 2015"
IGHGP_RAIL = "India GHG Program, India Specific Rail Transport Emission Factors, v1.0, 2015"
EPA_EFH = "US EPA Exposure Factors Handbook, ch. 6 (Sep 2011), Table 6-2, mean short-term inhalation rates"


@dataclass(frozen=True)
class Factor:
    value: float
    unit: str
    source: str


# CO₂ attributed to one traveller per km. Private and hired vehicles count the whole vehicle-km
# (the trip happens because of this traveller); shared transit counts one passenger's share.
CO2_PER_KM: dict[CommuteMode, Factor] = {
    CommuteMode.CAR: Factor(0.140, "kg CO2/vehicle-km", f"{IGHGP_ROAD}: hatchback <1400 cc petrol, with uplift"),
    CommuteMode.TWO_WHEELER: Factor(0.0368, "kg CO2/vehicle-km", f"{IGHGP_ROAD}: scooter <110 cc, with uplift"),
    CommuteMode.AUTO: Factor(0.10768, "kg CO2/vehicle-km", f"{IGHGP_ROAD}: three-wheeler, CNG"),
    CommuteMode.BUS: Factor(0.015161, "kg CO2/passenger-km", f"{IGHGP_ROAD}: intracity bus"),
    # No metro-specific factor is published by the programme; electric suburban rail is the closest.
    CommuteMode.METRO: Factor(0.00795, "kg CO2/passenger-km", f"{IGHGP_RAIL}: suburban rail (used for metro)"),
    CommuteMode.WALK: Factor(0.0, "kg CO2/km", "no fuel burned"),
    CommuteMode.CYCLE: Factor(0.0, "kg CO2/km", "no fuel burned"),
}
# Assumption: a carpool is three people sharing one car.
CARPOOL_OCCUPANCY = 3

# Breathing rate (m³/min) by age and effort, from EPA Table 6-2. Only ratios are used, so the
# figures' US origin matters less than their relative size: hard exercise moves 4x the air of light.
# Rows: (lowest age in the band, {intensity: rate}), youngest first.
_INHALATION_M3_PER_MIN: tuple[tuple[int, dict[Intensity, float]], ...] = (
    (3, {Intensity.LIGHT: 0.011, Intensity.MODERATE: 0.021, Intensity.HIGH: 0.037}),
    (6, {Intensity.LIGHT: 0.011, Intensity.MODERATE: 0.022, Intensity.HIGH: 0.042}),
    (11, {Intensity.LIGHT: 0.013, Intensity.MODERATE: 0.025, Intensity.HIGH: 0.049}),
    (16, {Intensity.LIGHT: 0.012, Intensity.MODERATE: 0.026, Intensity.HIGH: 0.049}),
    (21, {Intensity.LIGHT: 0.012, Intensity.MODERATE: 0.026, Intensity.HIGH: 0.050}),
    (31, {Intensity.LIGHT: 0.012, Intensity.MODERATE: 0.027, Intensity.HIGH: 0.049}),
    (41, {Intensity.LIGHT: 0.013, Intensity.MODERATE: 0.028, Intensity.HIGH: 0.052}),
    (51, {Intensity.LIGHT: 0.013, Intensity.MODERATE: 0.029, Intensity.HIGH: 0.053}),
    (61, {Intensity.LIGHT: 0.012, Intensity.MODERATE: 0.026, Intensity.HIGH: 0.047}),
    (71, {Intensity.LIGHT: 0.012, Intensity.MODERATE: 0.025, Intensity.HIGH: 0.047}),
    (81, {Intensity.LIGHT: 0.012, Intensity.MODERATE: 0.025, Intensity.HIGH: 0.048}),
)


def inhalation_rate(age: int, intensity: Intensity) -> float:
    """m³ of air breathed per minute (EPA_EFH). Under-3s use the 3-6 band."""
    rates = _INHALATION_M3_PER_MIN[0][1]
    for lowest_age, band_rates in _INHALATION_M3_PER_MIN:
        if age >= lowest_age:
            rates = band_rates
    return rates[intensity]


# Assumption: without a purifier, indoor PM2.5 equals outdoor. Delhi studies report winter
# indoor/outdoor ratios near or above 1, so walls alone are given no credit.
INDOOR_TO_OUTDOOR = Factor(1.0, "ratio", "assumption (conservative); Delhi winter studies report ratios of ~0.8-1.6")
PURIFIER_REDUCTION = Factor(
    0.49, "fraction of indoor PM2.5 removed",
    "Chen C-F et al., Int J Environ Res Public Health 2022 (PMC9516965): HEPA cleaner, 33.5 to 17.2 µg/m³")
# Sizing: AHAM's rule (CADR in cfm >= 2/3 of floor area in ft², at 8 ft ceilings) equals 5 air changes an hour.
PURIFIER_AIR_CHANGES_PER_HOUR = 5
ROOM_HEIGHT_M = 3.0  # assumption: a typical Indian ceiling
