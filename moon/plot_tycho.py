"""Interactive Mayavi surface plot of Tycho crater elevation

Call it from command line as `python -m moon.plot_tycho`
"""

import numpy as np
from mayavi import mlab
from moon import io as mio


def make_mayavi(warp_scale=0.1):
    """Plotting interactive crater DEM data with mayavi"""

    # TODO 1: use rasterio of tiff file
    #         img = rasterio.open('Lunar_LRO_LOLA_Global_LDEM_118m_Mar2014.tif')
    # TODO 2: rewrite this function to take in a crater name and some kind of
    #         radius around the border (radius-fractional + scalar paddning),
    #         then calculate the mapped region from lon/lat to array dimensions
    #         Some helpful references:
    #         https://stackoverflow.com/questions/36399374/
    #         https://stackoverflow.com/questions/38102927/
    #         (SCRATCH THAT JUST USE rasterio windows!)
    # TODO 3: use georeferencing and windows to carve out a crater window


    # need these to extract the lat / lon arrays from a Tycho cutout
    # surely there's a better way to do it (via pyproj) right?
    range_x = np.array([42400, 43850])
    range_y = np.array([33500, 34750])
    shape_large = np.array([46080, 92160])
    range_lon = range_x / shape_large[1] * 360 - 180
    range_lat = 90 - range_y / shape_large[0] * 180

    dem_tycho = mio.get_tycho_cutout(range_x, range_y)

    surf = mlab.surf(range_lon, range_lat, dem_tycho,
                     warp_scale=warp_scale, colormap='gist_earth')
    # TODO: can set a satellite texture on it with
    # surf.actor.actor.texture = optical_moon_image
    mlab.title("Tycho crater")
    mlab.colorbar(title='LOLA elevation model (m)', orientation='vertical',
                  label_fmt='%.1f')
    mlab.axes(xlabel='Longitude', ylabel='Latitude', zlabel='', opacity=0.5)
    ax = mlab.axes()
    #ax.axes.property.color = 'white'
    #ax.axes.axis_title_text_property.color = 'white'
    ax.axes.x_label = "Longitude"
    ax.axes.y_label = "Latitude"
    ax.axes.z_label = "Elevation"
    ax.axes.label_format = ""

    mlab.show()


if __name__ == '__main__':
    make_mayavi()
