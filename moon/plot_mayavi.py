"""
Interactive Mayavi surface plot of Tycho crater elevation

Call it from command line as `python -m moon.plot_tycho`
"""

from mayavi import mlab
from moon import io as mio


def make_figure(lon=-11.36, lat=-43.31, side=5, title=None, warp_scale=0.2):
    """Plotting interactive crater DEM data with mayavi"""

    range_lon = lon - side / 2, lon + side / 2
    range_lat = lat - side / 2, lat + side / 2

    # TODO: add reprojection to rasterio-based tiff handling
    #dem_arr = mio.square_cutout(lon, lat, side)
    dem_arr = mio.read_warped_window(lon, lat, side)

    surf = mlab.surf(range_lat, range_lon, dem_arr,
                     warp_scale=warp_scale, colormap='gist_earth')
    # TODO: can set a satellite texture on it with
    # surf.actor.actor.texture = optical_moon_image
    if title:
        mlab.title(title)
    mlab.colorbar(title='LOLA elevation model (m)', orientation='vertical',
                  label_fmt='%.1f')
    mlab.axes(xlabel='Longitude', ylabel='Latitude', zlabel='', opacity=0.5)
    ax = mlab.axes()
    #ax.axes.property.color = 'white'
    #ax.axes.axis_title_text_property.color = 'white'
    ax.axes.x_label = "Latitude"
    ax.axes.y_label = "Longitude"
    ax.axes.z_label = "Elevation"
    ax.axes.label_format = ""

    mlab.show()


if __name__ == '__main__':
    make_figure(lon=-11.36, lat=-43.31, side=4, title="Tycho crater")
