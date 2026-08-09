import numpy as np
import plotly.graph_objects as go
from astropy import time
from astropy import units as u
from poliastro.bodies import Mercury, Venus, Earth, Mars, Jupiter, Saturn, Uranus, Neptune, Sun
from poliastro.twobody import Orbit
from poliastro.ephem import Ephem
from poliastro.maneuver import Maneuver

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


def generate_porkchop_data(origin_name, dest_name, launch_date_str, transit_days, span=40, grid_resolution=25):
    """
    Generates a 2D grid of Delta-v requirements for various departure and arrival dates.
    Sweeps a window of +/- 'span' days around the user's selected baseline.
    """
    origin_body = PLANETS[origin_name]
    dest_body = PLANETS[dest_name]

    # 1. Center dates based on user input
    center_launch = time.Time(launch_date_str, scale="utc").tdb
    center_arrival = center_launch + transit_days * u.day

    # 2. Create arrays of time offsets
    launch_offsets = np.linspace(-span, span, grid_resolution)
    arrival_offsets = np.linspace(-span, span, grid_resolution)

    launch_epochs = center_launch + launch_offsets * u.day
    arrival_epochs = center_arrival + arrival_offsets * u.day

    dv_grid = np.zeros((grid_resolution, grid_resolution))

    for i, l_epoch in enumerate(launch_epochs):
        # Fetch Origin state
        orig_ephem = Ephem.from_body(origin_body, l_epoch)
        origin_orbit = Orbit.from_ephem(Sun, orig_ephem, l_epoch)

        for j, a_epoch in enumerate(arrival_epochs):
            if a_epoch <= l_epoch:
                dv_grid[j, i] = np.nan  # Time travel not allowed
                continue

            # Fetch Destination state
            dest_ephem = Ephem.from_body(dest_body, a_epoch)
            dest_orbit = Orbit.from_ephem(Sun, dest_ephem, a_epoch)

            try:
                # Solve Lambert's problem
                maneuver = Maneuver.lambert(origin_orbit, dest_orbit)
                dv1 = np.linalg.norm(maneuver.impulses[0][1].to(u.km / u.s).value)
                dv2 = np.linalg.norm(maneuver.impulses[1][1].to(u.km / u.s).value)
                dv_grid[j, i] = dv1 + dv2
            except Exception:
                # Lambert solver fails for non-physical/edge-case trajectories
                dv_grid[j, i] = np.nan

    # Convert astropy times to standard python datetimes for Plotly axes
    l_dates = [epoch.to_datetime() for epoch in launch_epochs]
    a_dates = [epoch.to_datetime() for epoch in arrival_epochs]

    return l_dates, a_dates, dv_grid


def create_porkchop_plot(launch_dates, arrival_dates, dv_grid):
    """
    Renders the Plotly contour map with a dark space theme.
    """
    # Cap the max Delta-v for the color scale so the plot isn't washed out by highly inefficient outliers
    min_dv = np.nanmin(dv_grid)
    max_dv_color = min_dv + 15.0  # Focus color scale strictly on the optimal windows

    fig = go.Figure(data=go.Contour(
        z=dv_grid,
        x=launch_dates,
        y=arrival_dates,
        colorscale='Inferno',  # A beautiful dark-to-bright heatmap scale
        zmin=min_dv,
        zmax=max_dv_color,
        contours=dict(
            start=min_dv,
            end=max_dv_color,
            size=0.5,
            showlabels=True,  # Label the contour lines with the dV amount
            labelfont=dict(size=10, color='white')
        ),
        colorbar=dict(title="Total Δv (km/s)"),
        hovertemplate="Launch: %{x|%Y-%m-%d}<br>Arrival: %{y|%Y-%m-%d}<br>Δv: %{z:.2f} km/s<extra></extra>"
    ))

    fig.update_layout(
        xaxis_title="Launch Date",
        yaxis_title="Arrival Date",
        template="plotly_dark",
        paper_bgcolor="black",
        plot_bgcolor="black",
        height=600,
        margin=dict(l=20, r=20, t=20, b=20)
    )

    return fig