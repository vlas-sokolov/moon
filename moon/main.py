"""
Playing around with Lunar elevation data

Explanation and full list of data references:
https://astrogeology.usgs.gov/search/map/Moon/LRO/LOLA/Lunar_LRO_LOLA_Global_LDEM_118m_Mar2014
"""

# FIXME: ... aren't the craters a bit too deep?!! The Tycho crater on a
#        (heavily downsampled) image looks ~8km deep, but the official depth
#        of Tycho is only 4.8 km bottom to the rim. What's going on?
#        UPDATE: not a downsampling issue - mayavi on original shows it too
# TODO: refactor this module out into modules/notebooks

import os
import numpy as np
import pandas as pd
from skimage.transform import downscale_local_mean
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
from cartopy import geodesic
import shapely
from moon.config import Paths, Constants
from moon import io as mio


def overplot_craters():
    """Overplot a lunar map with known crater outlines"""

    imdata_small = mio.load_lola_downsampled()
    smalldata = downscale_local_mean(imdata_small, factors=(10, 10))

    moon_globe = ccrs.Globe(ellipse=None,  # can remove after #1588/#564
                            semimajor_axis=Constants.moon_radius,
                            flattening=Constants.moon_flattening)
    moon_crs = ccrs.Robinson(globe=moon_globe)
    moon_transform = ccrs.PlateCarree(globe=moon_globe)

    plt.rc('text', usetex=True)
    fig = plt.figure(figsize=(12, 6), dpi=120)
    ax = plt.axes(projection=moon_crs)
    ax.gridlines(color='#252525', linestyle='dotted')
    im = ax.imshow(smalldata, origin="upper", transform=moon_transform)
    cbar = fig.colorbar(im, orientation='vertical', shrink=0.7)
    cbar.set_label(r'$\mathrm{LOLA~digital~elevation~model~(m)}$')
    ax.set_global()

    # Reference: International Astronomical Union (IAU) Planetary Gazetteer
    # CSV data downloaded from:  https://planetarynames.wr.usgs.gov/
    # Check the page here for all the history behind the moon feature naming:
    # https://the-moon.us/wiki/IAU_nomenclature
    iau_fname = os.path.join(Paths.table_dir, 'iau_approved_craters.csv')
    #iau_fname = os.path.join(Paths.table_dir, 'iau_approved_features.csv')
    iau_lunar_craters = pd.read_csv(iau_fname)
    lons = iau_lunar_craters.Center_Longitude
    lats = iau_lunar_craters.Center_Latitude
    radii_in_meters = iau_lunar_craters.Diameter * 500  # km to m
    moon_geodesic = geodesic.Geodesic(radius=Constants.moon_radius,
                                      flattening=Constants.moon_flattening)
    craters = []
    crater_proj = ccrs.Geodetic(globe=moon_globe)
    for lon, lat, radius in zip(lons, lats, radii_in_meters):
        if not radius:
            continue

        crater = moon_geodesic.circle(lon=lon, lat=lat, radius=radius,
                                      n_samples=15)
        craters.append(crater)
        geom = shapely.geometry.Polygon(crater)
        ax.add_geometries((geom,), crs=crater_proj, alpha=0.6,
                          facecolor='none', edgecolor='white', linewidth=0.5)

    plt.savefig(os.path.join(Paths.fig_dir, "lunar_craters.png"), dpi=120)


def tycho_mayavi(warp_scale=0.1):
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

    from mayavi import mlab

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


def main():
    """TODO: split this out into a notebook or something"""

    try:
        imdata_small = mio.load_lola_downsampled()
        moon_slice = np.load(os.path.join(Paths.data_dir, "lola_slice.npy"))
    except FileNotFoundError:
        # won't run on <16 GB RAM machine - look into
        # out-of-core solutions if that's ever an issue
        imdata_large = mio.load_lola_asarray()

        # We need to invoke a copy on a slice - otherwise the .base
        # .base attribute won't get released and the big array
        # will not get garbage collected!
        moon_slice = imdata_large[20000:30000, 20000:30000].copy()
        np.save(os.path.join(Paths.data_dir, "lola_slice.npy"), moon_slice)

        # radical downsampling for performance and profit
        imdata_small = mio.downsample_lola(imdata_large, n=5, save=True).copy()

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

    plt.figure(figsize=(6, 6))

    ax = plt.axes(projection=ccrs.Orthographic(-85, -15))
    ax.gridlines(color='#252525', linestyle='dotted')
    ax.imshow(imdata_small, origin="upper", extent=(-180, 180, -90, 90),
              transform=ccrs.PlateCarree())

    plt.savefig("moon.png", dpi=100)
    plt.show()


if __name__ == '__main__':
    main()