"""Convenience read/write functions for Lunar elevation data"""

import os
import numpy as np
from skimage import io as skimage_io
from skimage.transform import downscale_local_mean
from moon.config import Paths


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
