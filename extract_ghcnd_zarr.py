""" """
import numpy as np
import zarr
import datetime
import json
import calendar
import sys
import time

from multiprocessing import Pool
from pathlib import Path

field_convert = {
    "id":lambda v:str(v.strip()),
    "date":lambda v:datetime.date.strptime(v, "%Y%m%d"),
    "element":lambda v:v.strip(),
    "data_value":lambda v:int(v),
    "m_flag":lambda v:str(v.strip()),
    "q_flag":lambda v:str(v.strip()),
    "s_flag":lambda v:str(v.strip()),
    "obs_time":lambda v:str(v.strip()),
    }

element_name_mapping = {
    "PRCP":"precip", ## tenths of mm
    "SNOW":"snof", ## mm
    "SNWD":"snod", ## mm
    "TMAX":"tmax", ## tenths of degrees C
    "TMIN":"tmin", ## tenths of degrees C
    "MDSF":"mdsf", ## multi-day snowfall total
    "AWND":"wspd", ## average wind speed (m/s)
    "MDPR":"mdprecip", ## multi-day precip total
    "DAPR":"dapr", ## days of recorded precip in MDPR
    "DWPR":"dwpr", ## days with nonzero precip in MDPR
    }

element_dtypes = {
    "PRCP":np.float32,
    "SNOW":np.int16,
    "SNWD":np.int16,
    "TMAX":np.float32,
    "TMIN":np.float32,
    "MDSF":np.int16,
    "AWND":np.float32,
    "MDPR":np.float32,
    "DAPR":np.int16,
    "DWPR":np.int16,
    }

element_fill = {
    "PRCP":np.nan,
    "SNOW":-32768,
    "SNWD":-32768,
    "TMAX":np.nan,
    "TMIN":np.nan,
    "MDSF":-32768,
    "AWND":np.nan,
    "MDPR":np.nan,
    "DAPR":-32768,
    "DWPR":-32768,
    }

element_convert = {
    "PRCP":lambda v:v/10,
    "SNOW":lambda v:v,
    "SNWD":lambda v:v,
    "TMAX":lambda v:v/10,
    "TMIN":lambda v:v/10,
    "MDSF":lambda v:v,
    "AWND":lambda v:v/10,
    "MDPR":lambda v:v/10,
    "DAPR":lambda v:v,
    "DWPR":lambda v:v,
    }

def mp_parse_ghcnd_csv(args):
    return args,parse_ghcnd_csv(**args)

def parse_ghcnd_csv(csv_path:Path, year:int, extract_elements:list,
        station_meta_json:Path=None, valid_stations:list=None,
        lat_bounds=None, lon_bounds=None,
        ):
    """
    Parse a daily single-year GHCN file into a dictionary mapping station IDs
    to a dict of data variables (elements) supported by that station, and
    then each element to the full year of data, observation time, and flags
    for the measurement, quality, and source.
    """
    clines = csv_path.open("r").readlines()
    header = clines.pop(0)
    fields = [h.strip().lower() for h in header.split(",")]
    assert "date" in fields
    assert "element" in fields
    assert "data_value" in fields
    elix = fields.index("element")
    cdict = {fk:[] for fk in fields}
    smeta = None
    if station_meta_json is not None:
        smeta = json.load(station_meta_json.open("r"))
    print(f"processing {year} {time.perf_counter()}")
    sys.stdout.flush()

    for cs in clines:
        cl = cs.split(",")
        #print(cl)
        if field_convert["element"](cl[elix]) not in extract_elements:
            continue
        for fix,fk in enumerate(fields):
            cdict[fk].append(cl[fix])

    for ck in cdict.keys():
        cdict[ck] = [field_convert[ck](v) for v in cdict[ck]]
    del clines
    '''
    d = list(sorted(list(set(cdict["date"]))))
    all_dates = [
        d[0] + datetime.timedelta(days=i)
        for i in range((d[-1]-d[0]).days + 1)
        ]
    '''
    nd = 365 + int(calendar.isleap(year))
    all_dates = [
        datetime.date(year, 1, 1) + datetime.timedelta(days=i)
        for i in range(nd)
        ]
    svalid = set([])
    if valid_stations is not None:
        svalid = set(valid_stations)

    res = {}
    got_sids = []
    for i in range(len(cdict["date"])):
        sid = cdict["id"][i]
        if valid_stations is not None and not (sid in svalid):
            continue
        elif smeta is not None:
            sm = smeta[sid]
            if lat_bounds is not None:
                if not (lat_bounds[0] <= sm["lat"] <= lat_bounds[1]):
                    continue
            if lon_bounds is not None:
                if not (lon_bounds[0] <= sm["lon"] <= lon_bounds[1]):
                    continue
        got_sids.append(sid)

        ek = cdict["element"][i]
        dix = all_dates.index(cdict["date"][i])
        if sid not in res.keys():
            res[sid] = {}
        if ek not in res[sid].keys():
            da = np.full((nd,), element_fill[ek], dtype=element_dtypes[ek])
            res[sid][ek] = {
                "data_value":da,
                "obs_time":np.full((nd, 2), 255, dtype=np.uint8),
                "flags":np.full((nd,3), "", dtype="<U1"),
                }
        dv = cdict["data_value"][i]
        ot = cdict["obs_time"][i]
        try:
            if not (ot == ""):
                hhmm = np.asarray([int(ot[:2]), int(ot[2:])], dtype=np.uint8)
                res[sid][ek]["obs_time"][dix] = hhmm
            res[sid][ek]["data_value"][dix] = element_convert[ek](dv)
            res[sid][ek]["flags"][dix, 0] = cdict["m_flag"][i]
            res[sid][ek]["flags"][dix, 1] = cdict["q_flag"][i]
            res[sid][ek]["flags"][dix, 2] = cdict["s_flag"][i]
        except Exception as exc:
            print(year, sid, ek, cdict["date"][i])
            raise exc
    print(f"returning {year} {time.perf_counter()}")
    sys.stdout.flush()

    if valid_stations is None:
        valid_stations = got_sids

    tmp_obs = {}
    tmp_time = {}
    tmp_flags = {}
    for ek in extract_elements:
        tmp_obs[ek] = np.full(
            (len(valid_stations), nd),
            element_fill[ek],
            dtype=element_dtypes[ek],
            )
        tmp_time[ek] = np.full(
            (len(valid_stations), nd, 2),
            255,
            dtype=np.uint8,
            )
        tmp_flags[ek] = np.full(
            (len(valid_stations), nd, 3),
            "",
            dtype="<U1",
            )

    for six,sid in enumerate(valid_stations):
        sdict = res.get(sid, None)
        if sdict is None:
            continue
        for ek in extract_elements:
            edict = res[sid].get(ek, None)
            if edict is None:
                continue
            tmp_obs[ek][six] = edict["data_value"]
            tmp_time[ek][six] = edict["obs_time"]
            tmp_flags[ek][six] = edict["flags"]

    return all_dates,valid_stations,(tmp_obs,tmp_time,tmp_flags)

if __name__=="__main__":
    data_dir = Path("/discover/nobackup/mtdodson/GHCNd")
    source_dir = data_dir.joinpath("source/")
    store_path = data_dir.joinpath("GHCNd.zarr")
    #store_path = data_dir.joinpath("GHCNd_NAL.zarr")
    station_path = data_dir.joinpath("ghcnd-stations.json")

    year_range = (2001,2025)

    extract_elements = [
        "PRCP", "SNOW", "SNWD", "TMAX", "TMIN", "MDSF", "AWND",
        "MDPR", "DAPR",
        ]

    lat_bounds = (7, 72)
    lon_bounds = (-169, -52)
    #lat_bounds = (32.19, 35.07)
    #lon_bounds = (-88.3, -85.36)

    time_chunk_size = 65536
    time_shard_size = 65536 * 4
    station_chunk_size = 16
    station_shard_size = station_chunk_size * 2**10

    nworkers = 13

    """ -------------( end normal config )------------- """

    stations = json.load(station_path.open("r"))
    valid_stations = []
    locs = []
    for k,d in stations.items():
        if not (lat_bounds[0] <= d["lat"] <= lat_bounds[1]):
            continue
        if not (lon_bounds[0] <= d["lon"] <= lon_bounds[1]):
            continue
        valid_stations.append(k)
        locs.append(np.array([d["lat"], d["lon"], d["elev"]]))
    locs = np.stack(locs, axis=0)

    #assert not store_path.exists(), store_path.as_posix()

    tmpix = 0
    year_slices = {}
    for y in range(year_range[0], year_range[1]+1):
        nd = 365 + int(calendar.isleap(y))
        year_slices[y] = slice(tmpix, tmpix+nd)
        tmpix += nd
    total_days = tmpix

    zgrp = zarr.open(store_path, mode="a")

    zgrp.attrs.update({
        "fill_values":element_fill,
        })

    ## add latitude, longitude, and elevation of each station
    zgrp.create_array(
        "locations",
        shape=(len(valid_stations), 3),
        chunks=(station_chunk_size, 3),
        shards=(station_shard_size, 3),
        fill_value=np.nan,
        dtype=np.float32,
        dimension_names=["station", "lat_lon_elevation"],
        )
    zgrp["locations"][...] = locs

    ## add station IDs
    zgrp.create_array(
        "station",
        shape=(len(valid_stations),),
        chunks=(station_chunk_size,),
        shards=(station_shard_size,),
        fill_value="",
        dtype="U11",
        dimension_names=["station"],
        )
    zgrp["station"][...] = valid_stations

    ## create an array for all the dates
    zgrp.create_array(
        "date",
        shape=(total_days,),
        chunks=(total_days,),
        shards=(total_days,),
        dimension_names=["date"],
        dtype="M8[D]",
        )

    ## create groups for per-element observations, obs times, and flags
    zgrp.create_group("obs")
    zgrp.create_group("time")
    zgrp.create_group("flags")
    comp = zarr.codecs.BloscCodec(
        cname="zstd",
        clevel=4,
        shuffle="bitshuffle",
        typesize=4
        )
    for ek in extract_elements:
        zgrp["obs"].create_array(
            ek,
            shape=(len(valid_stations), total_days),
            chunks=(station_chunk_size, time_chunk_size),
            shards=(station_shard_size, time_shard_size),
            fill_value=element_fill[ek],
            dtype=element_dtypes[ek],
            dimension_names=["station", "date"],
            compressors=[comp],
            )
        zgrp["time"].create_array(
            ek,
            shape=(len(valid_stations), total_days, 2),
            chunks=(station_chunk_size, time_chunk_size, 2),
            shards=(station_shard_size, time_shard_size, 2),
            fill_value=255,
            dtype=np.uint8,
            dimension_names=["station", "date", "time"],
            compressors=[comp],
            )
        zgrp["flags"].create_array(
            ek,
            shape=(len(valid_stations), total_days, 3),
            chunks=(station_chunk_size, time_chunk_size, 1),
            shards=(station_shard_size, time_shard_size, 3),
            fill_value="",
            dtype="<U1",
            dimension_names=["station", "date", "flag"],
            compressors=[comp],
            )

    args = [{
        "csv_path":source_dir.joinpath(f"{y}.csv"),
        "year":y,
        "extract_elements":extract_elements,
        "valid_stations":valid_stations,
        #"station_meta_json":station_path,
        } for y in range(year_range[0], year_range[1]+1)]
    with Pool(nworkers) as pool:
        #for a,(d,r) in pool.imap_unordered(mp_parse_ghcnd_csv, args):
        for a,r in pool.imap_unordered(mp_parse_ghcnd_csv, args):
            d,_,(tmp_obs,tmp_time,tmp_flags) = r
            y = a["year"]
            yslc = year_slices[y]
            zgrp["date"][yslc] = d

            '''
            tmp_obs = {}
            tmp_time = {}
            tmp_flags = {}
            for ek in extract_elements:
                nslc = yslc.stop-yslc.start
                tmp_obs[ek] = np.full(
                    (len(valid_stations), nslc),
                    element_fill[ek],
                    dtype=element_dtypes[ek],
                    )
                tmp_time[ek] = np.full(
                    (len(valid_stations), nslc, 2),
                    255,
                    dtype=np.uint8,
                    )
                tmp_flags[ek] = np.full(
                    (len(valid_stations), nslc, 3),
                    "",
                    dtype="<U1",
                    )

            for six,sid in enumerate(valid_stations):
                sdict = r.get(sid, None)
                if sdict is None:
                    continue
                for ek in extract_elements:
                    edict = r[sid].get(ek, None)
                    if edict is None:
                        continue
                    tmp_obs[ek][six] = edict["data_value"]
                    tmp_time[ek][six] = edict["obs_time"]
                    tmp_flags[ek][six] = edict["flags"]
            '''

            for ek in extract_elements:
                ## if all empty, skip the variable and let it default
                ## to the fill value of the zarr array
                if np.all(tmp_obs[ek] == element_fill[ek]):
                    continue
                zgrp[f"/obs/{ek}"][:,yslc] = tmp_obs[ek]
                zgrp[f"/time/{ek}"][:,yslc] = tmp_time[ek]
                zgrp[f"/flags/{ek}"][:,yslc] = tmp_flags[ek]
            print(f"finished storing {y} {time.perf_counter()}")
            sys.stdout.flush()

    '''
    print("valid stations:", len(valid_stations))
    for y in year_range:
        yslc = year_slices[y]
        d,r = parse_ghcnd_csv(
            csv_path=source_dir.joinpath(f"{y}.csv"),
            year=y,
            extract_elements=extract_elements,
            valid_stations=valid_stations,
            )
        zgrp["date"][yslc] = d
        for six,sid in enumerate(valid_stations):
            sdict = r.get(sid, None)
            if sdict is None:
                continue
            for ek in extract_elements:
                edict = r[sid].get(ek, None)
                if edict is None:
                    continue
                zgrp[f"/obs/{ek}"][six,yslc] = edict["data_value"]
                zgrp[f"/time/{ek}"][six,yslc] = edict["obs_time"]
                zgrp[f"/flags/{ek}"][six,yslc] = edict["flags"]
        print(f"finished processing {y}")
    '''
