"""Toying around with moon globe rotatiton"""

import numpy as np
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import gif
from moon import load_lola_downsampled


@gif.frame
def make_frame(data, lon=-85, lat=-15):
    """Makes a globe frame for lon/lat pair"""

    plt.figure(figsize=(6, 6), dpi=100)

    # TODO: would passing a pre-made Globe instance speed things up?
    ax = plt.axes(projection=ccrs.Orthographic(lon, lat))
    ax.gridlines(color='#252525', linestyle='dotted')
    ax.imshow(data, origin="upper", extent=(-180, 180, -90, 90),
              transform=ccrs.PlateCarree())


def main():
    """Makes a spinning globe .gif of Moon elevation"""

    imdata_small = load_lola_downsampled()

    frames = []
    all_the_angles = np.linspace(0, 360, 25)[:-1]
    for i, lon in enumerate(all_the_angles):
        print(f"{i+1}/{all_the_angles.size}...")
        frame = make_frame(imdata_small, lon)
        frames.append(frame)

    gif.save(frames, "figures/moon.gif", duration=100)
