"""
Convenience read/write functions for Lunar elevation data

Includes some georeferencing tricks. Some more basic ones with rasterio/proj:
>>> xy_to_lonlat = Transformer.from_crs(crs, crs.geodetic_crs)
>>> lonlat_to_xy = Transformer.from_crs(crs.geodetic_crs, crs)

Example 1: pixel x/y to lon/lat:
>>> lon, lat = transformer.transform(*img.xy(10, 1))

Example 2: lon/lat to pixel x/y:
>>> x, y = img.index(*lonlat_to_xy.transform(-90, 45))

Example 3: find the centre of Tycho crater:
>>> x, y = img.index(*lonlat_to_xy.transform(-11.36, -43.31))
"""

import os
import numpy as np
import rasterio  # for proper crs-grokking GeoTiff loading
from pyproj import CRS, Transformer
from skimage import io as skimage_io  # if we just need a numpy array out of it
from skimage.transform import downscale_local_mean
from moon.config import Paths

# FIXME: need to re-project those cutouts on the fly - the edges on the map,
#        e.g., `square_cutout(0, -88, 2)`, look like rings of Jupiter,
#        and we can't wrap things around yet - so `square_cutout(0, -89, 2)`
#        throws an exception.

# Defining as a bunch of constants to avoid accidental reloading
LOLA_READER = rasterio.open(os.path.join(Paths.data_dir, Paths.tif_fname))
LOLA_CRS = CRS(LOLA_READER.crs)

# Transformation shortcuts - maaaybe I should not overuse constants here
XY_TO_LONLAT = Transformer.from_crs(LOLA_CRS, LOLA_CRS.geodetic_crs)
LONLAT_TO_XY = Transformer.from_crs(LOLA_CRS.geodetic_crs, LOLA_CRS)


def square_cutout(lon, lat, side):
    """Extracts a numpy array for a side-degrees square centered at lon/lat"""

    lower_x, lower_y = LONLAT_TO_XY.transform(lon - side, lat - side)
    upper_x, upper_y = LONLAT_TO_XY.transform(lon + side, lat + side)

    window = rasterio.windows.from_bounds(lower_x, lower_y,
                                          upper_x, upper_y,
                                          LOLA_READER.transform)
    return LOLA_READER.read(window=window)[0]  # only one channel


def load_lola_asarray():
    """Read the TIF file as an array. Don't keep it in RAM unless needed!"""

    try:
        # I haven't figured out how astrogeology folks normally load this;
        # my best guess is rasterio for lazy loading and header parsing?
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


def get_tycho_cutout(range_x=np.array([42400, 43850]),
                     range_y=np.array([33500, 34750])):
    """One-time shot at saving a numpy array slice of Tycho crater"""

    cutout_path = os.path.join(Paths.data_dir, 'tycho_crater.npy')
    try:
        dem_tycho = np.load(cutout_path)
    except FileNotFoundError:
        impath = os.path.join(Paths.data_dir, Paths.tif_fname)
        imdata = skimage_io.imread(impath)
        dem_tycho = imdata[slice(*range_y), slice(*range_x)]
        np.save(cutout_path, dem_tycho)

    return dem_tycho
