from astropy import time
from astropy import units as u
from poliastro.ephem import Ephem
from poliastro.bodies import Mercury, Venus, Earth, Mars, Jupiter, Saturn, Uranus, Neptune, Sun
from poliastro.twobody import Orbit

# A dictionary to map string names to poliastro body objects
PLANETS = {
    "Mercury": Mercury,
    "Venus": Venus,
    "Earth": Earth,
    "Mars": Mars,
    "Jupiter": Jupiter,
    "Saturn": Saturn,
    "Uranus": Uranus,
    "Neptune": Neptune
}

def get_planetary_orbits(origin_name, dest_name, launch_date_str, transit_days):
    """
    Fetches the planetary orbits for the selected origin and destination bodies.
    """
    # Parse dates
    launch_epoch = time.Time(launch_date_str, scale="utc").tdb
    arrival_epoch = launch_epoch + transit_days * u.day

    # Lookup the bodies dynamically
    origin_body = PLANETS[origin_name]
    dest_body = PLANETS[dest_name]

    # Fetch ephemerides
    origin_ephem = Ephem.from_body(origin_body, launch_epoch)
    dest_ephem = Ephem.from_body(dest_body, arrival_epoch)

    # Convert to standard two-body orbits with the SUN as the central attractor
    origin_orbit = Orbit.from_ephem(Sun, origin_ephem, launch_epoch)
    dest_orbit = Orbit.from_ephem(Sun, dest_ephem, arrival_epoch)

    return origin_orbit, dest_orbit, launch_epoch, arrival_epoch