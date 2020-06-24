"""Toying around with moon globe rotatiton"""

import os
import numpy as np
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import gif
from .config import Paths, Constants
from .moon import load_lola_downsampled


@gif.frame
def make_frame(data, globe, transform, lon=-85, lat=-15):
    """Makes a globe frame for lon/lat pair"""

    plt.figure(figsize=(6, 6), dpi=100)

    ax = plt.axes(projection=ccrs.Orthographic(lon, lat, globe=globe))
    ax.gridlines(color='#252525', linestyle='dotted')
    ax.imshow(data, origin="upper", transform=transform)


def main():
    """Makes a spinning globe .gif of Moon elevation"""

    imdata_small = load_lola_downsampled()

    moon_globe = ccrs.Globe(ellipse=None,  # can remove after #1588/#564
                            semimajor_axis=Constants.moon_radius,
                            flattening=Constants.moon_flattening)
    transform = ccrs.PlateCarree(globe=moon_globe)

    frames = []
    all_the_angles = np.linspace(0, 360, 25)[:-1]
    for i, lon in enumerate(all_the_angles):
        print(f"{i+1}/{all_the_angles.size}...")
        frame = make_frame(imdata_small, moon_globe, transform, lon)
        frames.append(frame)

    gif.save(frames, os.path.join(Paths.fig_dir, "moon.gif"), duration=100)
