"""Indian cities the app knows by name: where they are, and whether a metro is an option there.

A bundled list rather than a geocoding service: no extra network call, no key, and testable.
"Use my location" works anywhere; the nearest city here only labels it and answers the metro question.
Metro is marked only where a network serves everyday commutes, not where a first short stretch has opened.
"""

import math
from dataclasses import dataclass

EARTH_RADIUS_KM = 6371.0
# A place this far from every listed city gets no city label (and no metro suggestion).
CITY_RADIUS_KM = 40.0


@dataclass(frozen=True)
class City:
    name: str
    state: str
    lat: float
    lon: float
    has_metro: bool


CITIES: tuple[City, ...] = (
    City("Delhi", "Delhi", 28.6139, 77.2090, True),
    City("Noida", "Uttar Pradesh", 28.5355, 77.3910, True),
    City("Ghaziabad", "Uttar Pradesh", 28.6692, 77.4538, True),
    City("Gurugram", "Haryana", 28.4595, 77.0266, True),
    City("Faridabad", "Haryana", 28.4089, 77.3178, True),
    City("Mumbai", "Maharashtra", 19.0760, 72.8777, True),
    City("Navi Mumbai", "Maharashtra", 19.0330, 73.0297, True),
    City("Pune", "Maharashtra", 18.5204, 73.8567, True),
    City("Nagpur", "Maharashtra", 21.1458, 79.0882, True),
    City("Kolkata", "West Bengal", 22.5726, 88.3639, True),
    City("Bengaluru", "Karnataka", 12.9716, 77.5946, True),
    City("Chennai", "Tamil Nadu", 13.0827, 80.2707, True),
    City("Hyderabad", "Telangana", 17.3850, 78.4867, True),
    City("Ahmedabad", "Gujarat", 23.0225, 72.5714, True),
    City("Jaipur", "Rajasthan", 26.9124, 75.7873, True),
    City("Lucknow", "Uttar Pradesh", 26.8467, 80.9462, True),
    City("Kanpur", "Uttar Pradesh", 26.4499, 80.3319, True),
    City("Kochi", "Kerala", 9.9312, 76.2673, True),
    City("Chandigarh", "Chandigarh", 30.7333, 76.7794, False),
    City("Ludhiana", "Punjab", 30.9010, 75.8573, False),
    City("Amritsar", "Punjab", 31.6340, 74.8723, False),
    City("Agra", "Uttar Pradesh", 27.1767, 78.0081, False),
    City("Varanasi", "Uttar Pradesh", 25.3176, 82.9739, False),
    City("Prayagraj", "Uttar Pradesh", 25.4358, 81.8463, False),
    City("Patna", "Bihar", 25.5941, 85.1376, False),
    City("Dehradun", "Uttarakhand", 30.3165, 78.0322, False),
    City("Bhopal", "Madhya Pradesh", 23.2599, 77.4126, False),
    City("Indore", "Madhya Pradesh", 22.7196, 75.8577, False),
    City("Raipur", "Chhattisgarh", 21.2514, 81.6296, False),
    City("Ranchi", "Jharkhand", 23.3441, 85.3096, False),
    City("Guwahati", "Assam", 26.1445, 91.7362, False),
    City("Bhubaneswar", "Odisha", 20.2961, 85.8245, False),
    City("Visakhapatnam", "Andhra Pradesh", 17.6868, 83.2185, False),
    City("Vadodara", "Gujarat", 22.3072, 73.1812, False),
    City("Surat", "Gujarat", 21.1702, 72.8311, False),
    City("Jodhpur", "Rajasthan", 26.2389, 73.0243, False),
    City("Coimbatore", "Tamil Nadu", 11.0168, 76.9558, False),
    City("Thiruvananthapuram", "Kerala", 8.5241, 76.9366, False),
)


def distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance (haversine)."""
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi, d_lambda = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = math.sin(d_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    return 2 * EARTH_RADIUS_KM * math.asin(math.sqrt(a))


def nearest_city(lat: float, lon: float) -> City | None:
    """The closest listed city within CITY_RADIUS_KM, or None."""
    city = min(CITIES, key=lambda c: distance_km(lat, lon, c.lat, c.lon))
    return city if distance_km(lat, lon, city.lat, city.lon) <= CITY_RADIUS_KM else None
