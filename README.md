### What is this?

A small Python package aimed at extracting cutouts of lunar craters from a larger dataset of lunar elevation. The dataset is an 8 GB [digital elevation model](https://astrogeology.usgs.gov/search/map/Moon/LRO/LOLA/Lunar_LRO_LOLA_Global_LDEM_118m_Mar2014) based on the Lunar Orbiter Laser Altimeter (LOLA) data from NASA's Lunar Reconnaissance Orbiter spacecraft.

### What can it do?

For example, it can make a cutout around the Tycho crater and warp it to get rid of projection errors  (i.e. craters are circles, not ellipses), saving it into a .tif file:

```python
from moon import io as mio

mio.crater_cutout('tycho', destNameOrDestDS="tycho.tif", format="GTIFF")
```

Or a `flask` server can be started, serving the `.tif` cutouts via a (rudimentary) simple API:

On server side: `export FLASK_APP=lunar_api.py; python -m flask run`

On client side: `curl http://127.0.0.1:5000/craters\?name=tycho --output tycho.tif`

Open and plot the elevation with `rasterio`:

```python
import rasterio
import rasterio.plot as rioplot
import matplotlib.pyplot as plt

dem = rasterio.open('tycho.tif')
ax = rioplot.show(dem, title='Tycho crater')
ax.set_xlabel('meters')
ax.set_ylabel('meters')
```

![Tycho crater](https://github.com/vlas-sokolov/moon/blob/master/figures/tycho.png)

### References

- Explanation and full list of data references for LOLA dataset: [link](https://astrogeology.usgs.gov/search/map/Moon/LRO/LOLA/Lunar_LRO_LOLA_Global_LDEM_118m_Mar2014)
- Tables of lunar features come from the International Astronomical Union Planetary Gazetteer: can be downloaded as .csv [here](https://planetarynames.wr.usgs.gov/), with a good read on all the history behind the moon feature naming [here](https://the-moon.us/wiki/IAU_nomenclature)
