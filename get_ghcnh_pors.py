import zarr
import numpy as np
import datetime
import pickle as pkl
from pathlib import Path

if __name__=="__main__":
    store_path = Path("/discover/nobackup/mtdodson/GHCNh/GHCNh.zarr")
    out_pkl = Path("/discover/nobackup/mtdodson/GHCNh/ghcnh_records.pkl")
    start_date = datetime.date(2001, 1, 1)
    end_date = datetime.date(2025, 12, 31)

    zgrp = zarr.open(store_path, mode="r")

    all_dates = []
    date_ixs = {}
    for i in range(int((end_date-start_date).days) + 1):
        d = start_date + datetime.timedelta(days=i)
        if not d.year in date_ixs.keys():
            date_ixs[d.year] = {}
        if not d.month in date_ixs[d.year].keys():
            date_ixs[d.year][d.month] = {}
        if not d.month in date_ixs[d.year][d.month].keys():
            date_ixs[d.year][d.month][d.day] = {}
        date_ixs[d.year][d.month][d.day] = i
        all_dates.append(d)

    has_hours = []
    sids = list(zgrp["stations"])
    record_info = []
    for i,sid in enumerate(sids):
        zs = zgrp[f"/stations/{sid}"]
        pcp = zs["hourly"][7]
        ## if the station doesn't record precip, skip it
        if np.all(~np.isfinite(pcp)):
            continue
        times = zs["time"][...]
        times = times.astype("datetime64[us]").astype(datetime.datetime)
        tmph = np.full((len(all_dates),), 0, dtype=np.uint32)
        for t in times:
            tmph[date_ixs[t.year][t.month][t.day]] += 1
        record_info.append({
            "station_id":sid,
            "attrs":zs,
            "has_precip_zeros":bool(np.any(pcp == 0)),
            "station_codes":list([
                [int(v) for v in np.unique(zs["station_code"][i]) if v != -1]
                for i in range(zs["station_code"].shape[0])
                ]),
            })
        has_hours.append(tmph)
    has_hours = np.stack(has_hours, axis=0)
    print(has_hours.shape)
    print(np.count_nonzero(has_hours))
    pkl.dump([record_info, all_dates, has_hours], out_pkl.open("wb"))
