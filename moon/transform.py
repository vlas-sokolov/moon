"""Helper functions for Lunar georeferencing

Some example uses for directly using pyptoj+rasterio:
>>> xy_to_lonlat = Transformer.from_crs(crs, crs.geodetic_crs)
>>> lonlat_to_xy = Transformer.from_crs(crs.geodetic_crs, crs)

Example 1: pixel x/y to lon/lat:
>>> lon, lat = transformer.transform(*img.xy(10, 1))

Example 2: lon/lat to pixel x/y:
>>> x, y = img.index(*lonlat_to_xy.transform(-90, 45))

Example 3: find the centre of Tycho crater:
>>> x, y = img.index(*lonlat_to_xy.transform(-11.36, -43.31))
"""

# FIXME: need to re-project those cutouts on the fly - the edges on the map,
#        e.g., `square_cutout(0, -88, 2)`, look like rings of Jupyter,
#        and we can't wrap things around yet - so `square_cutout(0, -89, 2)`
#        throws an exception.

import os
import rasterio
from pyproj import CRS, Transformer
from moon.config import Paths


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
