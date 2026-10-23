import os
import numpy as np
import imageio.v2 as imageio
import plotly.io as pio

# Import your existing backend logic
from src.ephemeris import get_planetary_orbits
from src.trajectory import calculate_transfer
from src.visualization import create_mission_plot


def create_rotating_gif():
    print("Initializing astrodynamics engine...")

    # 1. Generate the base mission data (Earth to Mars)
    # Note: Adjust the arguments here if your get_planetary_orbits requires planet names
    earth_orbit, mars_orbit, launch_epoch, arrival_epoch = get_planetary_orbits("Earth", "Mars", "2026-10-30 12:00:00", 306)
    transfer_orbit, _, _, _ = calculate_transfer(earth_orbit, mars_orbit)
    fig = create_mission_plot(earth_orbit, mars_orbit, transfer_orbit, "Earth", "Mars")

    # 2. Setup a temporary folder for frames
    os.makedirs("temp_frames", exist_ok=True)
    frames = []

    # 3. Rotate camera and capture frames
    num_frames = 48  # Total frames in the GIF (higher = smoother, but larger file size)
    print(f"📸 Capturing {num_frames} frames...")

    for i in range(num_frames):
        # Calculate the camera angle (full 360-degree circle)
        angle = i * (2 * np.pi / num_frames)

        # Update the camera position using trigonometry
        camera = dict(
            up=dict(x=0, y=0, z=1),
            center=dict(x=0, y=0, z=0),
            eye=dict(x=2.5 * np.cos(angle), y=2.5 * np.sin(angle), z=1.2)
        )
        fig.update_layout(scene_camera=camera)

        # Save the frame to disk
        frame_path = f"temp_frames/frame_{i:03d}.png"
        fig.write_image(frame_path, width=800, height=600)
        frames.append(imageio.imread(frame_path))
        print(f"   Saved {frame_path}")

    # 4. Compile into a GIF
    print("🎬 Stitching frames into GIF...")
    os.makedirs("assets/screenshots", exist_ok=True)
    gif_path = "assets/screenshots/trajectory_demo.gif"

    # fps=15 gives a smooth, steady rotation speed
    imageio.mimsave(gif_path, frames, fps=15, loop=0)

    # 5. Clean up temporary files
    for file in os.listdir("temp_frames"):
        os.remove(f"temp_frames/{file}")
    os.rmdir("temp_frames")

    print(f"Success! GIF saved to {gif_path}")


if __name__ == "__main__":
    create_rotating_gif()