"""Because yaml is an overkill for a few string constants"""

import os


class Paths:
    """Paths, folders, URLs, and that sort of thing"""

    data_dir = os.path.expanduser("~/Projects/moon_lander/data/")
    table_dir = os.path.expanduser("~/Projects/moon_lander/tables/")
    fig_dir = os.path.expanduser("~/Projects/moon_lander/figures/")

    tif_fname = "Lunar_LRO_LOLA_Global_LDEM_118m_Mar2014.tif"
    tif_fname_small = "Lunar_LRO_LOLA_Downsampled.npy"

    tif_url = ("http://planetarymaps.usgs.gov/mosaic/"
               "Lunar_LRO_LOLA_Global_LDEM_118m_Mar2014.tif")


class Constants:
    """
    Geometrical definition for Lunar reference ellipsoid

    Ref: https://nssdc.gsfc.nasa.gov/planetary/factsheet/moonfact.html
    """

    # no need to specify the semiminor axis: `proj +a=xxx +f=yyy` is sufficient
    moon_radius = 1737100  # equatorial; in meters, naturally
    moon_flattening = 0.0012  # an oblateness [(a - b) / a] of the lunar model

    # absolute reference point for LOLA digital elevation model
    # TODO: they seem to have used a spherical model?
    moon_ref_radius = 1737400
