import numpy as np
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import pickle as pkl
from pathlib import Path

from plotting import plot_geo_points

if __name__=="__main__":
    por_pkl = Path("/discover/nobackup/mtdodson/GHCNh/ghcnh_records.pkl")
    store_path = Path("/discover/nobackup/mtdodson/GHCNh/GHCNh.zarr")
    fig_dir = Path("/home/mtdodson/scripts/ghcn/data/GHCNh/figures")

    lat_bounds = (7,72)
    lon_bounds = (-169,-52)

    record_info,all_dates,has_hours = pkl.load(por_pkl.open("rb"))
    all_months = {}
    month_strings = []
    for d in all_dates:
        tmps = d.strftime("%Y%m")
        if tmps not in all_months.keys():
            all_months[tmps] = {"lat":[], "lon":[], "nobs":[]}
        month_strings.append(tmps)

    month_slices = {}
    ix0 = 0
    for i in range(1, len(month_strings)):
        if month_strings[i] != month_strings[ix0]:
            month_slices[month_strings[ix0]] = slice(ix0, i)
            ix0 = i
    month_slices[month_strings[i]] = slice(ix0, len(month_strings))

    lat,lon,nobs = [],[],[]
    monthly = {}
    min_monthly_obs = None
    max_monthly_obs = None
    for i,station in enumerate(record_info):
        tmp_lat = float(station["attrs"]["lat"])
        tmp_lon = float(station["attrs"]["lon"])
        lat.append(tmp_lat)
        lon.append(tmp_lon)
        #nobs.append(np.sum(has_hours[i]))
        nobs.append(np.count_nonzero(has_hours[i]) / len(all_dates))
        for mk,mslc in month_slices.items():
            v = has_hours[i][mslc]
            #v = np.sum(np.count_nonzero(v) / v.size) ## days observed
            #v = np.sum(np.count_nonzero(v)) ## total num obs
            print(v.shape, np.amin(v), np.amax(v))
            v = np.sum(v) / v.size ## avg obs per day
            if v != 0:
                if min_monthly_obs is None or v < min_monthly_obs:
                    min_monthly_obs = v
                if max_monthly_obs is None or v > max_monthly_obs:
                    max_monthly_obs = v
                all_months[mk]["lat"].append(tmp_lat)
                all_months[mk]["lon"].append(tmp_lon)
                all_months[mk]["nobs"].append(v)
    exit(0)


    plot_geo_points(
        lat=lat,
        lon=lon,
        extent=[*lon_bounds, *lat_bounds],
        color_data=nobs,
        size_data=None,
        plot_spec={
            "title":"GHCNh Station Observation Count (2001-2025)",
            "cmap":"jet",
            "fig_size":(13,7),
            #"cbar_label":"Number of obs (2001-2025)",
            "cbar_label":"Fraction of days observed (2001-2025)",
            "size_range":(1,8),
            "cbar_pad":.02,
            "dpi":200,
            },
        out_path=fig_dir.joinpath("ghcnh_nobs_full-por.png"),
        show=False,
        )

    for mk,md in all_months.items():
        mstr = f"{mk[:4]} {mk[-2:]}"
        plot_geo_points(
            lat=md["lat"],
            lon=md["lon"],
            extent=[*lon_bounds, *lat_bounds],
            color_data=md["nobs"],
            size_data=None,
            plot_spec={
                "title":f"GHCNh Monthly Station Observation Count ({mstr})",
                "cmap":"jet",
                "fig_size":(13,7),
                "cbar_label":f"Mean num obs per day ({mstr})",
                #"cbar_label":f"Number of observations ({mstr})",
                #"cbar_label":f"Fraction of days observed ({mstr})",
                "size_range":(2,8),
                "cbar_pad":.02,
                "point_kwargs":{"marker":"."},
                "vmin":min_monthly_obs,
                "vmax":max_monthly_obs,
                "dpi":200,
                },
            out_path=fig_dir.joinpath(f"monthly/ghcnh_nobs_{mk}.png"),
            show=False,
            )
