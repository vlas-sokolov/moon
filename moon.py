"""
Playing around with Lunar elevation data

Explanation and full list of data references:
https://astrogeology.usgs.gov/search/map/Moon/LRO/LOLA/Lunar_LRO_LOLA_Global_LDEM_118m_Mar2014
"""

import os
import numpy as np
import pandas as pd
from skimage import io as skimage_io
from skimage.transform import downscale_local_mean
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
from cartopy import geodesic
import shapely
from config import DATA_DIR, TIF_FNAME, TIF_URL, TIF_FNAME_SMALL


# Ref: https://nssdc.gsfc.nasa.gov/planetary/factsheet/moonfact.html
MOON_RADIUS = 1737100  # equatorial; in meters, naturally
MOON_FLATTENING = 0.0012  # an oblateness [(a-b)/a] of our lunar model
# no need to specify the semiminor axis: `proj +a=xxx +f=yyy` is sufficient


def load_lola_asarray():
    """Read the TIF file as an array. Don't keep it in RAM unless needed!"""

    try:
        # I haven't figured out how astrogeology folks normally load this;
        # opencv seems to fail - maybe there's a dedicated package for this
        # that preserves the metadata but I got it working with skimage already
        impath = os.path.join(DATA_DIR, TIF_FNAME)
        imdata = skimage_io.imread(impath)
    except (FileNotFoundError, NotADirectoryError) as err:
        # auto-downloading massive TIF files on `except` is a pretty
        # bad idea, will raise an exception with a URL instead
        raise RuntimeError("Download the (warning: 8GB) image"
                           f" from {TIF_URL} first") from err

    return imdata


def downsample_lola(imdata, n=5, save=False, **kwargs):
    """
    Downsample the image by taking every n'th grid value

    Parameters
    ----------
    n : int, default: 5
        Grid downscaling factor.

    save : bool, default: False
        Whether to save the array under DATA_DIR.

    Returns
    -------
    smalldata : np.ndarray
        Downsampled LOLA image data.

    Other Parameters
    ----------------
    **kwargs
        All other keyword arguments are passed to
        `skimage.transform.downscale_local_mean`.
    """

    smalldata = downscale_local_mean(imdata, factors=(n, n), **kwargs)

    if save:
        np.save(os.path.join(DATA_DIR, TIF_FNAME_SMALL), smalldata)

    return smalldata


def load_lola_downsampled():
    """Read the previously downsampled NumPy array"""

    impath = os.path.join(DATA_DIR, TIF_FNAME_SMALL)
    imdata = np.load(impath)

    return imdata


def overplot_craters():
    """Overplot a lunar map with known crater outlines"""

    imdata_small = load_lola_downsampled()
    smalldata = downscale_local_mean(imdata_small, factors=(15, 15))

    plt.figure(figsize=(10, 10), dpi=100)
    moon_globe = ccrs.Globe(ellipse=None,  # can remove after #1588/#564
                            semimajor_axis=MOON_RADIUS,
                            flattening=MOON_FLATTENING)
    moon_crs = ccrs.Robinson(globe=moon_globe)
    moon_transform = ccrs.PlateCarree(globe=moon_globe)
    ax = plt.axes(projection=moon_crs)
    ax.gridlines(color='#252525', linestyle='dotted')
    ax.imshow(smalldata, origin="upper", transform=moon_transform)
    ax.set_global()

    # Reference: International Astronomical Union (IAU) Planetary Gazetteer
    # CSV data downloaded from:  https://planetarynames.wr.usgs.gov/
    # Check the page here for all the history behind the moon feature naming:
    # https://the-moon.us/wiki/IAU_nomenclature
    iau_lunar_craters = pd.read_csv('iau_approved_craters.csv')
    #iau_lunar_craters = pd.read_csv('iau_approved_features.csv')
    lons = iau_lunar_craters.Center_Longitude
    lats = iau_lunar_craters.Center_Latitude
    radii_in_meters = iau_lunar_craters.Diameter * 500  # km to m
    moon_geodesic = geodesic.Geodesic(radius=MOON_RADIUS,
                                      flattening=MOON_FLATTENING)
    craters = []
    crater_proj = ccrs.Geodetic(globe=moon_globe)
    for lon, lat, radius in zip(lons, lats, radii_in_meters):
        if not radius:
            continue

        crater = moon_geodesic.circle(lon=lon, lat=lat, radius=radius,
                                      n_samples=15)
        craters.append(crater)
        geom = shapely.geometry.Polygon(crater)
        ax.add_geometries((geom,), crs=crater_proj, alpha=1.0,
                          facecolor='none', edgecolor='red', linewidth=0.5)

    plt.savefig("moon_features.png", dpi=100)


def main():
    """TODO: split this out into a notebook or something"""

    try:
        imdata_small = load_lola_downsampled()
        moon_slice = np.load(os.path.join(DATA_DIR, "lola_slice.npy"))
    except FileNotFoundError:
        # won't run on <16 GB RAM machine - look into
        # out-of-core solutions if that's ever an issue
        imdata_large = load_lola_asarray()

        # We need to invoke a copy on a slice - otherwise the .base
        # .base attribute won't get released and the big array
        # will not get garbage collected!
        moon_slice = imdata_large[20000:30000, 20000:30000].copy()
        np.save(os.path.join(DATA_DIR, "lola_slice.npy"), moon_slice)

        # radical downsampling for performance and profit
        imdata_small = downsample_lola(imdata_large, n=5, save=True).copy()

        # FIXME this doesn't always release memory - I may have left
        #       a reference to a big array somewhere - but where?
        del imdata_large

    # the whole image is too large to display! slices of it look awesome though
    # .ipynb this
    #plt.imshow(moon_slice)
    #plt.show()

    # downsampled image can be viewed
    # .ipynb this
    #plt.imshow(imdata_small)
    #plt.show()

    plt.figure(figsize=(6, 6))

    ax = plt.axes(projection=ccrs.Orthographic(-85, -15))
    ax.gridlines(color='#252525', linestyle='dotted')
    ax.imshow(imdata_small, origin="upper", extent=(-180, 180, -90, 90),
              transform=ccrs.PlateCarree())

    plt.savefig("moon.png", dpi=100)
    plt.show()


if __name__ == '__main__':
    main()
