import streamlit as st
import datetime

# Import modular backend components
from src.ephemeris import get_planetary_orbits
from src.ephemeris import PLANETS
from src.trajectory import calculate_transfer, parking_orbit_dv
from src.visualization import create_mission_plot
from src.porkchop import generate_porkchop_data, create_porkchop_plot


# --- CACHING OVERHEAD ---
@st.cache_data(show_spinner=False)
def get_planetary_orbits_cached(origin, dest, launch_time_str, transit_days):
    """Wraps the ephemeris fetching in Streamlit's cache to prevent redundant API calls."""
    return get_planetary_orbits(origin, dest, launch_time_str, transit_days)


@st.cache_data(show_spinner=False)
def get_porkchop_cached(origin, dest, launch_time_str, transit_days):
    """Caches the heavy porkchop grid computation."""
    # Note: We need to update the porkchop module to accept origin/dest too.
    return generate_porkchop_data(origin, dest, launch_time_str, transit_days, span=40, grid_resolution=25)


# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Orbital Trajectory Planner", layout="wide")
st.title("Interplanetary Trajectory Planner")
st.markdown(
    "Configure your mission parameters in the sidebar to visualize the transfer trajectory and calculate energy requirements.")

# --- SIDEBAR: USER INPUTS ---
st.sidebar.header("Mission Parameters")

# Planet Selection Dropdowns
planets = ["Mercury", "Venus", "Earth", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune"]
origin_planet = st.sidebar.selectbox("Origin Planet", planets, index=2)  # Default Earth
dest_planet = st.sidebar.selectbox("Destination Planet", planets, index=3)  # Default Mars

if origin_planet == dest_planet:
    st.sidebar.error("Origin and Destination cannot be the same.")
    st.stop()  # Halt execution until they pick different planets

launch_date_input = st.sidebar.date_input(
    "Select Launch Date",
    datetime.date(2026, 10, 30),
    help="Default: near the minimum-energy Earth → Mars launch of the 2026 window.",
)
transit_days = st.sidebar.slider("Transit time (days)", 60, 600, 306)
parking_alt = st.sidebar.number_input("Parking-orbit altitude (km)", 100, 2000, 200, 50,
                                      help="Circular orbit the spacecraft departs from and is captured into.")

# Format time string for Astropy
launch_time_str = f"{launch_date_input} 12:00:00"

# --- MAIN EXECUTION ---
try:
    # Create modern tabs for the UI
    tab_3d, tab_porkchop = st.tabs(["🪐 3D Mission Visualization", "📈 Launch Window Analysis (Porkchop)"])

    with tab_3d:
        with st.spinner("Calculating ephemerides, Lambert solution, and trajectories..."):
            # 1. Fetch data with dynamic planets
            origin_orbit, dest_orbit, launch_epoch, arrival_epoch = get_planetary_orbits_cached(
                origin_planet, dest_planet, launch_time_str, transit_days
            )

            # 2. Compute physics
            transfer_orbit, vinf_dep, vinf_arr, vinf_sum = calculate_transfer(
                origin_orbit, dest_orbit
            )
            dv_dep = parking_orbit_dv(vinf_dep, PLANETS[origin_planet], parking_alt)
            dv_arr = parking_orbit_dv(vinf_arr, PLANETS[dest_planet], parking_alt)

            # Feasibility check
            if vinf_sum > 15.0:
                st.sidebar.warning(
                    f"⚠️ **High v∞ ({vinf_sum:.2f} km/s):** these dates are far from a launch window. "
                    "Check the porkchop plot for cheaper dates.")

            # 3. Render visuals with dynamic names
            fig = create_mission_plot(origin_orbit, dest_orbit, transfer_orbit, origin_planet, dest_planet)

            # --- RENDER TO SCREEN ---
            st.plotly_chart(fig, use_container_width=True)

    with tab_porkchop:
        st.markdown(
            "Sweeps a ±40 day window around your selected dates. Colour is the sum of departure and arrival v∞ from Lambert's problem; **darker regions are cheaper**.")
        with st.spinner("Computing 625 Lambert transfers for grid map... (Takes ~2 seconds)"):
            l_dates, a_dates, dv_grid = get_porkchop_cached(origin_planet, dest_planet, launch_time_str, transit_days)
            fig_porkchop = create_porkchop_plot(l_dates, a_dates, dv_grid)
            st.plotly_chart(fig_porkchop, use_container_width=True)

    # Output Metrics to Sidebar
    st.sidebar.markdown("---")
    st.sidebar.subheader("Mission Epochs")
    st.sidebar.write(f"**Departure:** {launch_epoch.iso[:10]} (UTC)")
    st.sidebar.write(f"**Arrival:** {arrival_epoch.iso[:10]} (UTC)")

    st.sidebar.markdown("---")
    st.sidebar.subheader("Hyperbolic excess speed (Lambert)")
    st.sidebar.write(f"**Departure v∞:** {vinf_dep:.2f} km/s  (C3 = {vinf_dep**2:.1f} km²/s²)")
    st.sidebar.write(f"**Arrival v∞:** {vinf_arr:.2f} km/s")
    st.sidebar.subheader(f"Burns from/into a {parking_alt} km circular orbit (patched conic)")
    st.sidebar.write(f"**Departure Δv:** {dv_dep:.2f} km/s")
    st.sidebar.write(f"**Capture Δv:** {dv_arr:.2f} km/s")
    st.sidebar.write(f"**Total Δv:** {dv_dep + dv_arr:.2f} km/s")

except Exception as e:
    st.error(f"An error occurred during calculation: {e}")
    st.markdown(
    "This is likely due to the Lambert solver failing to find a valid trajectory for the specific combination of dates and transit time. Try adjusting the transit time slider or launch date.")