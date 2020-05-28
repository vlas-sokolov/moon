"""
Playing around with Lunar elevation data

Explanation and full list data references:
https://astrogeology.usgs.gov/search/map/Moon/LRO/LOLA/Lunar_LRO_LOLA_Global_LDEM_118m_Mar2014
"""

import os
import logging
import numpy as np
import matplotlib.pyplot as plt
from config import DATA_DIR, TIF_FNAME, TIF_FNAME_SMALL


def load_lola_asarray():
    """Read the TIF file as an array. Don't keep it in RAM unless needed!"""

    try:
        # I haven't figured out how astrogeology folks normally load this;
        # opencv seems to fail - maybe there's a dedicated package for this
        # that preserves the metadata but I got it working with skimage already
        from skimage import io
        impath = os.path.join(DATA_DIR, TIF_FNAME)
        imdata = io.imread(impath)
    except (FileNotFoundError, NotADirectoryError) as err:
        # auto-downloading massive TIF files on `except` is a pretty
        # bad idea, will raise an exception with a URL instead
        from config import TIF_URL
        raise RuntimeError("Download the (warning: 8GB) image"
                           f" from {TIF_URL} first") from err

    return imdata


def downsample_lola(imdata, n=5, save=False): # pylint: disable=invalid-name
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
    """

    # TODO: ideally should be interpolated, otherwise we're losing data!
    smalldata = imdata[::n, ::n]

    if save:
        np.save(os.path.join(DATA_DIR, TIF_FNAME_SMALL), smalldata)

    return smalldata


def load_lola_downsampled():
    """Read the previously downsampled NumPy array"""

    impath = os.path.join(DATA_DIR, TIF_FNAME_SMALL)
    imdata = np.load(impath)

    return imdata


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

    import cartopy.crs as ccrs
    plt.figure(figsize=(3, 3))

    ax = plt.axes(projection=ccrs.Orthographic(-45, 15))
    ax.gridlines(color='black', linestyle='dotted')
    ax.imshow(imdata_small, origin="upper", extent=(-180, 180, -90, 90),
              transform=ccrs.PlateCarree())

    plt.show()
