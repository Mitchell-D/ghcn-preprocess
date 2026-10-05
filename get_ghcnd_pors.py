import numpy as np
import zarr
import pickle as pkl
from multiprocessing import Pool
from pathlib import Path

if __name__=="__main__":
    data_dir = Path("/discover/nobackup/mtdodson/GHCNd")
    store_path = data_dir.joinpath("GHCNd.zarr")
    out_pkl = data_dir.joinpath("ghcnd_records.pkl")

    zgrp = zarr.open(store_path, mode="r")

    qflags = zgrp["flags/PRCP"][...,1]
    m_quality = ~(qflags == "")
    pcp = zgrp["obs/PRCP"][...]
    pcp[m_quality] = np.nan
    pcp = np.isfinite(pcp).astype(np.uint8)
    locs = zgrp["locations"][...]
    sflags = zgrp["flags/PRCP"][...,2]

    record_info = []
    sids = zgrp["station"][...].tolist()
    for i in range(len(sids)):
        record_info.append({
            "station_id":sids[i],
            "attrs":{
                "lat":locs[i][0],
                "lon":locs[i][1],
                "elev":locs[i][2],
                },
            "station_codes":list(np.unique(sflags[i]))
            })

    dates = zgrp["date"][...].astype(object)
    pkl.dump([record_info, dates, pcp], out_pkl.open("wb"))
