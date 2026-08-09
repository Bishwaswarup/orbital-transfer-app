import numpy as np
from poliastro.maneuver import Maneuver
from astropy import units as u


def calculate_transfer(earth_orbit, mars_orbit):
    """
    Solves Lambert's problem to calculate the transfer trajectory and required Delta-v.
    """
    maneuver = Maneuver.lambert(earth_orbit, mars_orbit)

    # intermediate=True gives (transfer_orbit_after_departure, final_orbit_after_arrival)
    # We unpack the tuple and keep only the first element (the transfer path)
    transfer_orbit, _ = earth_orbit.apply_maneuver(maneuver, intermediate=True)

    dv1_vector = maneuver.impulses[0][1]
    dv2_vector = maneuver.impulses[1][1]

    dv_departure = np.linalg.norm(dv1_vector.to(u.km / u.s).value)
    dv_arrival = np.linalg.norm(dv2_vector.to(u.km / u.s).value)
    total_dv = dv_departure + dv_arrival

    return transfer_orbit, dv_departure, dv_arrival, total_dv