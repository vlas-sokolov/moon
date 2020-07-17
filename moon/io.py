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
from functools import wraps
import numpy as np
import gdal
import rasterio  # for proper crs-grokking GeoTiff loading
from pyproj import CRS, Transformer
from skimage import io as skimage_io  # if we just need a numpy array out of it
from skimage.transform import downscale_local_mean
from moon.config import Paths

# Defining as a bunch of constants to avoid accidental reloading
LOLA_READER = rasterio.open(os.path.join(Paths.data_dir, Paths.tif_fname))
LOLA_CRS = CRS(LOLA_READER.crs)

# Transformation shortcuts - maaaybe I should not overuse constants here
XY_TO_LONLAT = Transformer.from_crs(LOLA_CRS, LOLA_CRS.geodetic_crs)
LONLAT_TO_XY = Transformer.from_crs(LOLA_CRS.geodetic_crs, LOLA_CRS)

# NOTE: a bit of a gotcha - the pixel values are *not* elevation! *gasp*
# Turns out that LOLA DEM have a scaling factor:
# height = (pixel_value * scaling_factor)
# And actual surface height (local radius) formula is:
# local_radius = (pixel_value * scaling_factor) + 1737400 meters
# Reference:
# https://astrogeology.usgs.gov/search/map/Moon/LRO/LOLA/Lunar_LRO_LOLA_Global_LDEM_118m_Mar2014
# ... I wonder why they went with the 0.5 factor to begin with?
SCALING_FACTOR = 0.5


def apply_scaling_factor(image_loader):
    """Applies a scaling factor to a return array of the decorated function"""

    @wraps(image_loader)
    def scaler_wrapper(*args, **kwargs):
        return SCALING_FACTOR * image_loader(*args, **kwargs)

    return scaler_wrapper


@apply_scaling_factor
def square_cutout(lon, lat, side):
    """Extracts a numpy array for a side-degrees square centered at lon/lat"""

    # FIXME: rewrite rasterio.warp! As a workaround, use the GDAL-based
    #        read_warped_window function to get rid of projection errors

    window = rasterio.windows.from_bounds(*square_lonlat_to_xy(lon, lat, side),
                                          transform=LOLA_READER.transform)
    return LOLA_READER.read(window=window)[0]  # only one channel


def square_lonlat_to_xy(lon, lat, side):
    """Converts a square of lon/lat centre and degrees size to x/y box"""

    lower_x, lower_y = LONLAT_TO_XY.transform(lon - side / 2, lat - side / 2)
    upper_x, upper_y = LONLAT_TO_XY.transform(lon + side / 2, lat + side / 2)

    return lower_x, lower_y, upper_x, upper_y


@apply_scaling_factor
def read_warped_window(lon, lat, side, width_correction=True,
                       source=os.path.join(Paths.data_dir, Paths.tif_fname)):
    """The GDAL way, although ideally I should rewrite this in rasterio.warp"""

    try:
        side_lat, side_lon = side
    except TypeError:
        side_lat, side_lon = side, side

    # Apply a rough correction on the width (~1/cos(lat) for equirectangular)
    if width_correction:
        side_lon /= np.cos(lat / 180 * np.pi)

    lat_min, lat_max = lat - side_lat / 2, lat + side_lat / 2
    lon_min, lon_max = lon - side_lon / 2, lon + side_lon / 2

    cut = gdal.Warp('', source,
                    format='MEM', resampleAlg=gdal.GRA_CubicSpline,
                    multithread=True,
                    outputBounds=(lon_min, lat_min, lon_max, lat_max),
                    outputBoundsSRS="+proj=longlat +no_defs",
                    srcSRS="+proj=eqc +R=1737400",
                    dstSRS=f"+proj=ortho +lat_0={lat} +lon_0={lon}"
                           " +R=1737400 +no_defs")

    return cut.ReadAsArray()


def load_lola_asarray():
    """Read the TIF file as an array. Don't keep it in RAM unless needed!"""

    try:
        # It seems that GDAL (or something on top of it like rasterio) is a
        # clear winner in loading the .tif image. The following below is sort
        # of a legacy code I used for downsampling the image.
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


@apply_scaling_factor
def load_lola_downsampled():
    """Read the previously downsampled NumPy array"""

    impath = os.path.join(Paths.data_dir, Paths.tif_fname_small)
    imdata = np.load(impath)

    return imdata


@apply_scaling_factor
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
