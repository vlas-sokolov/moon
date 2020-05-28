"""Because yaml is an overkill for a few string constants"""

import os

DATA_DIR = os.path.expanduser("~/Projects/moon_lander/data/")
TIF_FNAME = "Lunar_LRO_LOLA_Global_LDEM_118m_Mar2014.tif"
TIF_FNAME_SMALL = "Lunar_LRO_LOLA_Downsampled.npy"

TIF_URL = ("http://planetarymaps.usgs.gov/mosaic/"
           "Lunar_LRO_LOLA_Global_LDEM_118m_Mar2014.tif")
