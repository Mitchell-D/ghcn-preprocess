import numpy as np
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from pathlib import Path

def plot_geo_points(lat, lon, extent, color_data=None, size_data=None,
        plot_spec={}, out_path=None, show=False,
        ):
    """
    :@param lat: Size N 1d array of latitudes for each point
    :@param lon: Size N 1d array of longitudes for each point
    :@param color_data: Optional size N 1d array of data values represented
        by the size of each point.
    :@param color_data: Optional size N 1d array of data values represented
        by the mapped color of the value.
    :@param plot_spec:
    """
    ps = {
        "title":"",
        "projection":ccrs.PlateCarree(),
        "cmap":"jet",
        "size_range":(30,150), ## min/max marker size in points
        "cbar":True,
        "cbar_label":None,
        "cbar_pad":.02,
        "cbar_shrink":.8,
        "point_kwargs":{}, ## passed to ax.scatter
        "fig_size":(10,6),
        "dpi":120,
        }
    ps.update(plot_spec)
    lon = np.asarray(lon)
    lat = np.asarray(lat)

    if lon.shape != lat.shape:
        raise ValueError("lon and lat must have the same shape")

    ## validate optional data.
    if color_data is not None:
        color_data = np.asarray(color_data)
        if color_data.shape != lon.shape:
            raise ValueError("color_data must have the same shape as lon/lat.")
    if size_data is not None:
        size_data = np.asarray(size_data)
        if size_data.shape != lon.shape:
            raise ValueError("size_data must have the same shape as lon/lat.")

    ## normalize sizes to the requested point range
    if size_data is not None:
        smin,smax = ps.get("size_range")
        v_min = np.nanmin(size_data)
        v_max = np.nanmax(size_data)

        if v_max == v_min:
            sizes = np.full_like(size_data, (smin+smax)/2, dtype=float)
        else:
            sizes = smin + ((size_data-v_min)/(v_max-v_min))*(smax-smin)
    else:
        sizes = ps.get("size_range")[0]

    '''
    fig,ax = plt.subplots(
        figsize=ps.get("fig_size"),
        subplot_kw={"projection":ps.get("projection")},
        )
    '''
    fig = plt.figure(figsize=ps.get("fig_size"), dpi=ps.get("dpi"))
    ax = fig.add_subplot(1,1,1, projection=ps.get("projection"))

    ax.set_extent(extent, crs=ccrs.PlateCarree())
    ax.add_feature(cfeature.STATES, edgecolor="gray")
    ax.add_feature(cfeature.COASTLINE)
    ax.tick_params(top=False, right=False)
    gl = ax.gridlines(draw_labels=True, alpha=0.4)
    gl.top_labels = False
    gl.right_labels = False
    fig.subplots_adjust(top=0.9)
    ax.set_title(ps.get("title"), pad=12)

    scatter = ax.scatter(
        lon,
        lat,
        s=sizes,
        c=color_data,
        cmap=ps.get("cmap") if color_data is not None else None,
        transform=ccrs.PlateCarree(),
        vmin=ps.get("vmin"),
        vmax=ps.get("vmax"),
        **ps.get("point_kwargs"),
        )

    if color_data is not None and ps.get("cbar"):
        cbar = fig.colorbar(
            scatter,
            ax=ax,
            pad=ps.get("cbar_pad"),
            shrink=ps.get("cbar_shrink")
            )
        if ps.get("cbar_label") is not None:
            cbar.set_label(ps.get("cbar_label"))

    if out_path is not None:
        fig.savefig(out_path, dpi=ps.get("dpi"))
    if show:
        plt.show()

