import numpy as np
from poliastro.maneuver import Maneuver
from astropy import units as u


def calculate_transfer(origin_orbit, dest_orbit):
    """Solve Lambert's problem between two heliocentric planet states.

    Returns the transfer orbit and the hyperbolic excess speeds v∞ at
    departure and arrival (km/s): the difference between the Lambert
    velocities and the planets' own heliocentric velocities. These are not
    the burns a spacecraft makes; see ``parking_orbit_dv`` for those.
    """
    maneuver = Maneuver.lambert(origin_orbit, dest_orbit)

    # intermediate=True gives (transfer_orbit_after_departure, final_orbit_after_arrival)
    transfer_orbit, _ = origin_orbit.apply_maneuver(maneuver, intermediate=True)

    vinf_departure = np.linalg.norm(maneuver.impulses[0][1].to(u.km / u.s).value)
    vinf_arrival = np.linalg.norm(maneuver.impulses[1][1].to(u.km / u.s).value)
    return transfer_orbit, vinf_departure, vinf_arrival, vinf_departure + vinf_arrival


def parking_orbit_dv(vinf_km_s, body, altitude_km=200.0):
    """Impulsive burn (km/s) between a circular parking orbit and a hyperbola with speed v∞.

    Patched-conic: at periapsis radius r the hyperbolic speed is
    sqrt(v∞² + 2μ/r) and the circular speed is sqrt(μ/r); the burn is their
    difference. The same expression gives the departure burn from a parking
    orbit and the capture burn into one.
    """
    mu = body.k.to(u.km**3 / u.s**2).value
    r = body.R.to(u.km).value + altitude_km
    return float(np.sqrt(vinf_km_s**2 + 2 * mu / r) - np.sqrt(mu / r))
