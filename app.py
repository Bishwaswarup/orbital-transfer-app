import streamlit as st
import datetime

# Import modular backend components
from src.ephemeris import get_planetary_orbits
from src.trajectory import calculate_transfer
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
    datetime.date(2026, 8, 9)
)
transit_days = st.sidebar.slider("Estimated Transit Time (Days)", 100, 400, 250)

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
            transfer_orbit, dv_dep, dv_arr, total_dv = calculate_transfer(
                origin_orbit, dest_orbit
            )

            # Feasibility check
            if total_dv > 15.0:
                st.sidebar.warning(
                    f"⚠️ **High Δv Detected ({total_dv:.2f} km/s):** This trajectory requires immense energy and may not be feasible for standard chemical propulsion. Try adjusting the transit time.")

            # 3. Render visuals with dynamic names
            fig = create_mission_plot(origin_orbit, dest_orbit, transfer_orbit, origin_planet, dest_planet)

            # --- RENDER TO SCREEN ---
            st.plotly_chart(fig, use_container_width=True)

    with tab_porkchop:
        st.markdown(
            "Sweeps a ±40 day window around your selected dates to find optimal, low-energy launch windows. **Darker regions indicate less fuel required.**")
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
    st.sidebar.subheader("Delta-v Estimates (Patched-Conic)")
    st.sidebar.write(f"**Departure dV:** {dv_dep:.2f} km/s")
    st.sidebar.write(f"**Arrival dV:** {dv_arr:.2f} km/s")
    st.sidebar.write(f"**Total dV:** {total_dv:.2f} km/s")

except Exception as e:
    st.error(f"An error occurred during calculation: {e}")
    st.markdown(
    "This is likely due to the Lambert solver failing to find a valid trajectory for the specific combination of dates and transit time. Try adjusting the transit time slider or launch date.")