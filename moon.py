"""
Playing around with Lunar elevation data

Explanation and full list of data references:
https://astrogeology.usgs.gov/search/map/Moon/LRO/LOLA/Lunar_LRO_LOLA_Global_LDEM_118m_Mar2014
"""

# FIXME: ... aren't the craters a bit too deep?!! The Tycho crater on a
#        (heavily downsampled) image looks ~8km deep, but the official depth
#        of Tycho is only 4.8 km bottom to the rim. What's going on?

import os
import numpy as np
import pandas as pd
from skimage import io as skimage_io
from skimage.transform import downscale_local_mean
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
from cartopy import geodesic
import shapely
from config import Paths, Constants


def load_lola_asarray():
    """Read the TIF file as an array. Don't keep it in RAM unless needed!"""

    try:
        # I haven't figured out how astrogeology folks normally load this;
        # opencv seems to fail - maybe there's a dedicated package for this
        # that preserves the metadata but I got it working with skimage already
        impath = os.path.join(Paths.data_dir, Paths.tif_fname)
        imdata = skimage_io.imread(impath)
    except (FileNotFoundError, NotADirectoryError) as err:
        # auto-downloading massive TIF files on `except` is a pretty
        # bad idea, will raise an exception with a URL instead
        raise RuntimeError("Download the (warning: 8GB) image"
                           f" from {Paths.tif_url} first") from err

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
        np.save(os.path.join(Paths.data_dir, Paths.tif_fname_small), smalldata)

    return smalldata


def load_lola_downsampled():
    """Read the previously downsampled NumPy array"""

    impath = os.path.join(Paths.data_dir, Paths.tif_fname_small)
    imdata = np.load(impath)

    return imdata


def overplot_craters():
    """Overplot a lunar map with known crater outlines"""

    imdata_small = load_lola_downsampled()
    smalldata = downscale_local_mean(imdata_small, factors=(10, 10))

    moon_globe = ccrs.Globe(ellipse=None,  # can remove after #1588/#564
                            semimajor_axis=Constants.moon_radius,
                            flattening=Constants.moon_flattening)
    moon_crs = ccrs.Robinson(globe=moon_globe)
    moon_transform = ccrs.PlateCarree(globe=moon_globe)

    plt.rc('text', usetex=True)
    fig = plt.figure(figsize=(12, 6), dpi=120)
    ax = plt.axes(projection=moon_crs)
    ax.gridlines(color='#252525', linestyle='dotted')
    im = ax.imshow(smalldata, origin="upper", transform=moon_transform)
    cbar = fig.colorbar(im, orientation='vertical', shrink=0.7)
    cbar.set_label(r'$\mathrm{LOLA~digital~elevation~model~(m)}$')
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
    moon_geodesic = geodesic.Geodesic(radius=Constants.moon_radius,
                                      flattening=Constants.moon_flattening)
    craters = []
    crater_proj = ccrs.Geodetic(globe=moon_globe)
    for lon, lat, radius in zip(lons, lats, radii_in_meters):
        if not radius:
            continue

        crater = moon_geodesic.circle(lon=lon, lat=lat, radius=radius,
                                      n_samples=15)
        craters.append(crater)
        geom = shapely.geometry.Polygon(crater)
        ax.add_geometries((geom,), crs=crater_proj, alpha=0.6,
                          facecolor='none', edgecolor='white', linewidth=0.5)

    plt.savefig(os.path.join(Paths.fig_dir, "lunar_craters.png"), dpi=120)


def tycho_mayavi(warp_scale=0.1):
    """Plotting interactive crater DEM data with mayavi"""

    from mayavi import mlab

    # need these to extract the lat / lon arrays from a Tycho cutout
    # surely there's a better way to do it (via pyproj) right?
    range_x = np.array([42400, 43850])
    range_y = np.array([33500, 34750])
    shape_large = np.array([46080, 92160])
    range_lon = range_x / shape_large[1] * 360 - 180
    range_lat = 90 - range_y / shape_large[0] * 180

    cutout_path = os.path.join(Paths.data_dir, 'tycho_crater.npy')
    try:
        dem_tycho = np.load(cutout_path)
    except FileNotFoundError:
        impath = os.path.join(Paths.data_dir, Paths.tif_fname)
        imdata = skimage_io.imread(impath)
        dem_tycho = imdata[slice(*range_y), slice(*range_x)]
        np.save(cutout_path, dem_tycho)

    surf = mlab.surf(range_lon, range_lat, dem_tycho,
                     warp_scale=warp_scale, colormap='gist_earth')
    # TODO: can set a satellite texture on it with
    # surf.actor.actor.texture = optical_moon_image
    mlab.title("Tycho crater")
    mlab.colorbar(title='LOLA elevation model (m)', orientation='vertical',
                  label_fmt='%.1f')
    mlab.axes(xlabel='Longitude', ylabel='Latitude', zlabel='', opacity=0.5)
    ax = mlab.axes()
    #ax.axes.property.color = 'white'
    #ax.axes.axis_title_text_property.color = 'white'
    ax.axes.x_label = "Longitude"
    ax.axes.y_label = "Latitude"
    ax.axes.z_label = "Elevation"
    ax.axes.label_format = ""


def main():
    """TODO: split this out into a notebook or something"""

    try:
        imdata_small = load_lola_downsampled()
        moon_slice = np.load(os.path.join(Paths.data_dir, "lola_slice.npy"))
    except FileNotFoundError:
        # won't run on <16 GB RAM machine - look into
        # out-of-core solutions if that's ever an issue
        imdata_large = load_lola_asarray()

        # We need to invoke a copy on a slice - otherwise the .base
        # .base attribute won't get released and the big array
        # will not get garbage collected!
        moon_slice = imdata_large[20000:30000, 20000:30000].copy()
        np.save(os.path.join(Paths.data_dir, "lola_slice.npy"), moon_slice)

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
