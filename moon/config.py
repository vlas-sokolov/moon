"""Because yaml is an overkill for a few string constants"""

import os
import numpy as np


class Paths:
    """Paths, folders, URLs, and that sort of thing"""

    data_dir = os.path.expanduser("~/Projects/moon_lander/data/")
    table_dir = os.path.expanduser("~/Projects/moon_lander/tables/")
    fig_dir = os.path.expanduser("~/Projects/moon_lander/figures/")

    tif_fname = "Lunar_LRO_LOLA_Global_LDEM_118m_Mar2014.tif"
    tif_fname_small = "Lunar_LRO_LOLA_Downsampled.npy"

    # Reference: International Astronomical Union (IAU) Planetary Gazetteer
    # CSV data downloaded from:  https://planetarynames.wr.usgs.gov/
    # Check the page here for all the history behind the moon feature naming:
    # https://the-moon.us/wiki/IAU_nomenclature
    iau_craters_fname = "iau_approved_craters.csv"
    iau_features_fname = "iau_approved_features.csv"

    tif_url = ("http://planetarymaps.usgs.gov/mosaic/"
               "Lunar_LRO_LOLA_Global_LDEM_118m_Mar2014.tif")


class Constants:
    """
    Geometrical definition for lunar reference ellipsoid

    Ref: https://nssdc.gsfc.nasa.gov/planetary/factsheet/moonfact.html
    """

    # no need to specify the semiminor axis: `proj +a=xxx +f=yyy` is sufficient
    moon_radius = 1737100  # equatorial; in meters, naturally
    moon_flattening = 0.0012  # an oblateness [(a - b) / a] of the lunar model

    # absolute reference point for LOLA digital elevation model
    # they seem to use a spherical model, not an oblate spheroid above
    lola_dem_moon_radius = 1737400
    lola_dem_scaling_factor = 0.5

    @classmethod
    def local_radius(cls, pixel_value, absolute=False):
        """Converts pixel value to local radius"""

        # NOTE: this a bit of a gotcha - the pixel values are *not* elevation!
        # Turns out that LOLA DEM have a scaling factor:
        # height = (pixel_value * scaling_factor)
        # And actual surface height (local radius) formula is:
        # local_radius = (pixel_value * scaling_factor) + 1737400 meters
        # Reference:
        # https://astrogeology.usgs.gov/search/map/Moon/LRO/ \
        #       LOLA/Lunar_LRO_LOLA_Global_LDEM_118m_Mar2014
        # Q: Why did they go with the 0.5 factor to begin with?
        # A: To make the files smaller? You can reduce the abs. error on DEM if
        #    your scaling factor is a float - DEM can be an 8-bit integer then

        elevation = pixel_value * cls.lola_dem_scaling_factor

        if absolute:
            return elevation + cls.lola_dem_moon_radius

        return elevation

    @classmethod
    def km_to_deg(cls, dist):
        """Returns corresponding degree for a given arc length of a circle"""

        # conversions: meters to km; rad to deg
        return dist / cls.lola_dem_moon_radius * 1000 / np.pi * 180
