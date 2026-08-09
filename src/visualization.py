import plotly.io as pio
from poliastro.plotting import OrbitPlotter3D

def create_mission_plot(origin_orbit, dest_orbit, transfer_orbit, origin_name, dest_name):
    """
    Generates an interactive 3D plot of the solar system and the transfer trajectory.
    """
    plotter = OrbitPlotter3D()

    # Dynamically assign labels based on user selection
    plotter.plot(origin_orbit, label=f"{origin_name} (At Departure)", color="deepskyblue")
    plotter.plot(dest_orbit, label=f"{dest_name} (At Arrival)", color="darkorange")
    plotter.plot(transfer_orbit, label="Transfer Trajectory", color="crimson")

    # In poliastro 0.17.0, .show() updates the layout and returns the Plotly figure
    fig = plotter.show()

    # Format the layout for the web app with a space-themed dark mode and angled camera
    fig.update_layout(
        height=650,
        margin=dict(l=0, r=0, t=0, b=0),
        template="plotly_dark",
        paper_bgcolor="black",
        scene_camera=dict(
            eye=dict(x=1.5, y=1.5, z=0.5)  # Modest elevation for better orbital viewing
        )
    )

    return fig