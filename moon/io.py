"""
Image operations and convenience read/write functions for lunar elevation data

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
from moon.config import Paths, Constants
from moon.features import LunarFeatures

# defining as a bunch of constants to avoid accidental reloading
try:
    LOLA_READER = rasterio.open(os.path.join(Paths.data_dir, Paths.tif_fname))
except rasterio.errors.RasterioIOError:
    # If the file isn't in the data dir, try reading from the S3 bucket instead
    LOLA_READER = rasterio.open(Paths.s3_url)

LOLA_CRS = CRS(LOLA_READER.crs)

# transformation shortcuts - maaaybe I should not overuse constants here
XY_TO_LONLAT = Transformer.from_crs(LOLA_CRS, LOLA_CRS.geodetic_crs)
LONLAT_TO_XY = Transformer.from_crs(LOLA_CRS.geodetic_crs, LOLA_CRS)


def _lonlat_to_xy_transform(lon, lat, lunar_r):
    return Transformer.from_crs(CRS(f"+proj=longlat +R={lunar_r} +lat_0={lat}"
                                    f" +lon_0={lon} +no_defs"), LOLA_CRS)

# TODO: the scaling factor is nice and all but it changes int8 into float64,
#       leading to increased data file size. If the goal is to make small
#       GeoTiff cutouts to be sent over the network, then the scaling factor
#       should *absolutely* be applied on the client side!
def apply_scaling_factor(image_loader):
    """Applies a scaling factor to a return array of the decorated function"""

    @wraps(image_loader)
    def scaler_wrapper(*args, **kwargs):
        image = image_loader(*args, **kwargs)

        # not everything is scalable! case in point - read_warped_window will
        # return None if we choose to write into a file and not load into MEM
        # numpy won't let us check if an array is None via bool()
        if not isinstance(image, np.ndarray) and not image:
            return image

        return Constants.local_radius(image, absolute=False)
    return scaler_wrapper


@apply_scaling_factor
def square_cutout(lon, lat, side, convert_km_to_deg=False):
    """Extracts a numpy array for a given square centered at lon/lat"""

    if convert_km_to_deg:
        side = Constants.km_to_deg(side)

    # FIXME: rewrite with rasterio.warp! As a workaround, use the GDAL-based
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
def read_warped_window(lon, lat, side,  # side can be either in deg or km
                       width_correction=True, convert_km_to_deg=False,
                       source=os.path.join(Paths.data_dir, Paths.tif_fname),
                       **kwargs):
    """The GDAL way, although ideally I should rewrite this in rasterio.warp"""

    # might not be the most sensible way of setting defaults but hey it works
    out_format = kwargs.pop("format", "MEM")
    destination = kwargs.pop("destNameOrDestDS", "")

    try:
        side_lat, side_lon = side
    except TypeError:
        side_lat, side_lon = side, side

    if convert_km_to_deg:
        side_lat = Constants.km_to_deg(side_lat)
        side_lon = Constants.km_to_deg(side_lon)

    # apply a rough correction on the width (~1/cos(lat) for equirectangular)
    if width_correction:
        side_lon /= np.cos(lat / 180 * np.pi)

    lat_min, lat_max = lat - side_lat / 2, lat + side_lat / 2
    lon_min, lon_max = lon - side_lon / 2, lon + side_lon / 2

    lunar_r = Constants.lola_dem_moon_radius

    # TODO: figure out how to transform the bounds first?
    # what is +nodefs then?
    dst_crs = CRS({"proj": "ortho", "lat_0": lat, "lon_0": lon, "R": lunar_r})
    cutout_bounds = [*LONLAT_TO_XY.transform(lon_min, lat_min),
                     *LONLAT_TO_XY.transform(lon_max, lat_max)]
    src_bounds_crs = CRS({"proj": "longlat", "R": lunar_r})
    src_crs = CRS({"proj": "eqc", "R": lunar_r})

    # added "+R=..." to outputBoundsSRS/te_srs to avoid errors in GDAL v3.x.x
    # cut = gdal.Warp(destNameOrDestDS=destination, srcDSOrSrcDSTab=source,
    #                 format=out_format, resampleAlg=gdal.GRA_CubicSpline,
    #                 multithread=True,
    #                 outputBounds=(lon_min, lat_min, lon_max, lat_max),
    #                 outputBoundsSRS=f"+proj=longlat +R={lunar_r} +no_defs",
    #                 srcSRS=f"+proj=eqc +R={lunar_r}",
    #                 dstSRS=f"+proj=ortho +lat_0={lat} +lon_0={lon}"
    #                        f" +R={lunar_r} +no_defs",
    #                 **kwargs)
    from rasterio.warp import calculate_default_transform
    transform, _, _ = calculate_default_transform(
            src_crs, src_bounds_crs,
            source.width, source.height,
            *cutout_bounds)  # FIXME this is nonsense!

    cut = rasterio.warp.reproject(
        source=source,
        destination=destination,
        src_crs=src_crs,
        dst_transform=transform,
        dst_crs=dst_crs,
        resampling=rasterio.warp.Resampling.cubic)

    if not cut:
        return cut

    return cut.ReadAsArray()


def crater_cutout(crater_name, pad=1.3, **kwargs):
    """Returns warped elevation model around a known crater"""

    lunar_features = LunarFeatures()  # ~100 ns to init, not an issue
    lat, lon, diameter = lunar_features.crater_position_size(crater_name)

    return read_warped_window(lon, lat, diameter*pad, convert_km_to_deg=True,
                              **kwargs)


def load_lola_asarray():
    """Read the TIF file as an array. Don't keep it in RAM unless needed!"""

    try:
        # it seems that GDAL (or something on top of it like rasterio) is a
        # clear winner in loading the .tif image. The following below is sort
        # of a legacy code I used for downsampling the image.
        from skimage import io as skimage_io
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

    from skimage.transform import downscale_local_mean
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
        from skimage import io as skimage_io
        impath = os.path.join(Paths.data_dir, Paths.tif_fname)
        imdata = skimage_io.imread(impath)
        dem_tycho = imdata[slice(*range_y), slice(*range_x)]
        np.save(cutout_path, dem_tycho)

    return dem_tycho
