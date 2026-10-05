"""
For each yearly .tar.gz of all stations:

Within each annual station file,  the station name, year, latitude, longitude,
elevation,
"""
import numpy as np
import zarr
import datetime

from multiprocessing import Pool
from pathlib import Path

#"temperature_Measurement_Code":"temp_meas_code",
#"temperature_Quality_Code":"temp_quality",
#"temperature_Report_Type":"temp_type",

def extract_ghcn_psv(
        psv_file:Path, extract_data_vars, extract_datetime_vars,
        extract_station_vars, extract_source_codes, extract_quality_flags,
        lat_bounds=None, lon_bounds=None, min_measurements=None,
        ):
    """
    Extract data from a single GHRCh station-year .psv file

    :@return: (
        station: single tuple of station vars
        time: 1d array of datetime64[ns] values for each time step
        data: 2d (var, time) array of float32 data values for each time step
        source_code: 2d (sc_var, time) array of int16 source codes per time
        quality_flag: 2d (qf_var, time) array of int16 quality flags per time
        )
    """
    assert psv_file.exists()
    lines = psv_file.open("r").readlines()
    header = lines.pop(0).split("|")
    if not min_measurements is None and len(lines) < min_measurements:
        return None
    ## get file field indices
    file_ixs = []
    assert "LATITUDE" in extract_station_vars
    ix_lat = extract_station_vars.index("LATITUDE")
    assert "LONGITUDE" in extract_station_vars
    ix_lon = extract_station_vars.index("LONGITUDE")
    for fk in extract_station_vars:
        file_ixs.append(header.index(fk))
    ## get variable field indices
    var_ixs = []
    for vk in extract_data_vars:
        var_ixs.append(header.index(vk))
    ## get time field indices
    time_ixs = []
    for tk in extract_datetime_vars:
        time_ixs.append(header.index(tk))
    ## get source code indices
    scode_ixs = []
    for sck in extract_source_codes:
        scode_ixs.append(header.index(sck))
    ## get quality flag indices
    qflag_ixs = []
    for qfk in extract_quality_flags:
        qflag_ixs.append(header.index(qfk))
    x = np.full((len(var_ixs), len(lines)), np.nan, dtype=np.float32)
    t = np.empty((len(lines),), dtype="datetime64[ns]")
    q = np.full((len(qflag_ixs), len(lines)), " ", dtype="U")
    s = np.full((len(scode_ixs), len(lines)), -1, dtype=np.int16)
    f = None
    for i,l in enumerate(lines):
        lsplit = l.split("|")
        ## load file field only on first iteration
        if f is None:
            f = tuple([lsplit[lix] for lix in file_ixs])
            lat = float(f[ix_lat])
            lon = float(f[ix_lon])
            if lat_bounds and not (lat_bounds[0] <= lat <= lat_bounds[1]):
                return None
            if lon_bounds and not (lon_bounds[0] <= lon <= lon_bounds[1]):
                return None
        ## load time as datetime64[ns]
        tstrs = [lsplit[tix] for tix in time_ixs]
        t[i] = datetime.datetime(*list(map(int, tstrs)))
        ## load data values as float32
        v = list(map(float, [
            lsplit[vix] if lsplit[vix] != "" else np.nan
            for vix in var_ixs
            ]))
        v = np.asarray(v, dtype=np.float32)
        x[:,i] = v
        ## load quality flags as characters
        q[:,i] = np.array([
            lsplit[qix] if lsplit[qix] != "" else " "
            for qix in qflag_ixs
            ])
        ## load source codes as ints
        s[:,i] = np.array([
            lsplit[six] if lsplit[six] != "" else -1
            for six in scode_ixs
            ])
    return f,t,x,s,q

def _append_ghcnh_to_zarr(zarr_path, extract_result, station_var_keys,
        time_shard_size=262144, time_chunk_size=65536,
        ):
    station,time,data,scode,qflag = extract_result
    assert len(station_var_keys) == len(station)
    assert "id" in station_var_keys
    sdict = dict(zip(station_var_keys, station))
    sid = sdict["id"]
    zgrp = zarr.open(zarr_path, mode="a")
    if not sid in zgrp["stations"].keys():
        zgrp_s = zgrp["stations"].create_group(sid)
        zgrp_s.attrs.update({"info":sdict})
        zgrp_s.create_array(
            "time",
            shape=time.shape,
            chunks=(time_chunk_size,),
            shards=(time_shard_size,),
            dimension_names=["time"],
            dtype=time.dtype,
            )
        zgrp_s.create_array(
            "hourly",
            shape=data.shape,
            chunks=(1, time_chunk_size),
            shards=(data.shape[0], time_shard_size),
            dimension_names=["time", "data_vars"],
            dtype=data.dtype,
            compressors=[
                zarr.codecs.BloscCodec(
                    cname="zstd",
                    clevel=4,
                    shuffle="bitshuffle",
                    typesize=4
                    )
                ],
            )
        zgrp_s.create_array(
            "station_code",
            shape=scode.shape,
            chunks=(1, time_chunk_size),
            shards=(scode.shape[0], time_shard_size),
            dimension_names=["time", "station_codes"],
            dtype=scode.dtype,
            compressors=[
                zarr.codecs.BloscCodec(
                    cname="zstd",
                    clevel=4,
                    shuffle="bitshuffle",
                    typesize=4
                    )
                ],
            )
        zgrp_s.create_array(
            "quality_flag",
            shape=qflag.shape,
            chunks=(1, time_chunk_size),
            shards=(qflag.shape[0], time_shard_size),
            dimension_names=["time", "quality_flags"],
            dtype=qflag.dtype,
            )
        zgrp_s["time"][...] = time
        zgrp_s["hourly"][...] = data
        zgrp_s["station_code"][...] = scode
        zgrp_s["quality_flag"][...] = qflag
    else:
        n = time.shape[0] + zgrp_s["time"].shape[0]
        zgrp_s["time"].resize(n)
        zgrp_s["hourly"].resize(n, zgrp_s["data"].shape[1])
        zgrp_s["station_code"].resize(n, zgrp_s["station_code"].shape[1])
        zgrp_s["quality_flag"].resize(n, zgrp_s["quality_flag"].shape[1])
        zgrp_s["time"][-n:] = time
        zgrp_s["data"][-n:,:] = data
        zgrp_s["station_code"][-n:,:] = scode
        zgrp_s["quality_flag"][-n:,:] = qflag

def _mp_ghcnh_extract_and_append(args):
    return args,_ghcnh_extract_and_append(**args)

def _ghcnh_extract_and_append(extract_args, append_args):
    extract_result = extract_ghcn_psv(**extract_args)
    if extract_result is None:
        return None
    append_args = {
        **append_args,
        "extract_result":extract_result,
        }
    _append_ghcnh_to_zarr(**append_args)
    return True

if __name__=="__main__":
    #source_dir = Path("/discover/nobackup/mtdodson/GHCNh/source/")
    source_dir = Path("/discover/nobackup/mtdodson/GHCNh/psv-combined/")
    #tmp_file = source_dir.joinpath("GHCNh_USW00064776_2025.psv")
    store_path = Path("/discover/nobackup/mtdodson/GHCNh/GHCNh.zarr")
    nworkers = 20

    ## minimum number of measurements to extract a station, since some of
    ## them are extremely sporadic
    min_num_measure = 100

    lat_bounds = (7, 72)
    lon_bounds = (-169, -52)

    extract_station_vars = [
        ("STATION", "id"),
        ("Station_name", "name"),
        ("LATITUDE", "lat"),
        ("LONGITUDE", "lon"),
        ("ELEVATION", "elev"),
        ]

    extract_data_vars = [
        ("temperature", "temp"),
        ("dew_point_temperature", "dewp"),
        ("station_level_pressure", "pres"),
        ("sea_level_pressure", "slpres"),
        ("wind_direction", "wdir"),
        ("wind_speed", "wspd"),
        ("wind_gust", "wgust"),
        ("precipitation", "precip"),
        ("relative_humidity", "rh"),
        ("snow_depth", "snod"),
        ]

    extract_source_codes = [
        ("temperature_Source_Code", "sc-temp"),
        ("dew_point_temperature_Source_Code", "sc-dewp"),
        ("station_level_pressure_Source_Code", "sc-pres"),
        ("sea_level_pressure_Source_Code", "sc-slpres"),
        ("wind_direction_Source_Code", "sc-wdir"),
        ("wind_speed_Source_Code", "sc-wspd"),
        ("wind_gust_Source_Code", "sc-wgust"),
        ("precipitation_Source_Code", "sc-precip"),
        ("relative_humidity_Source_Code", "sc-rh"),
        ("snow_depth_Source_Code", "sc-rh"),
        ]

    extract_quality_flags = [
        ("temperature_Quality_Code", "qc-temp"),
        ("dew_point_temperature_Quality_Code", "qc-dewp"),
        ("station_level_pressure_Quality_Code", "qc-pres"),
        ("sea_level_pressure_Quality_Code", "qc-slpres"),
        ("wind_direction_Quality_Code", "qc-wdir"),
        ("wind_speed_Quality_Code", "qc-wspd"),
        ("wind_gust_Quality_Code", "qc-wgust"),
        ("precipitation_Quality_Code", "qc-precip"),
        ("relative_humidity_Quality_Code", "qc-rh"),
        ("snow_depth_Quality_Code", "qc-snod"),
        ]

    extract_datetime_vars = ("Year", "Month", "Day", "Hour", "Minute")

    src_paths = [
        p for p in source_dir.iterdir()
        if p.suffix == ".psv" and p.stem.split("_")[0] == "GHCNh"
        ]
    src_years = {}
    for p in src_paths:
        _,sid,yyyy = p.stem.split("_")
        if yyyy not in src_years.keys():
            src_years[yyyy] = []
        src_years[yyyy].append(p)

    zgrp = zarr.open(store_path, mode="w")
    zgrp.create_group("stations")

    for yyyy in list(sorted(src_years.keys())):
        args = [{
            "extract_args":{
                "psv_file":p,
                "extract_station_vars":tuple(zip(*extract_station_vars))[0],
                "extract_data_vars":tuple(zip(*extract_data_vars))[0],
                "extract_source_codes":tuple(zip(*extract_source_codes))[0],
                "extract_quality_flags":tuple(zip(*extract_quality_flags))[0],
                "extract_datetime_vars":extract_datetime_vars,
                "lat_bounds":lat_bounds,
                "lon_bounds":lon_bounds,
                "min_measurements":min_num_measure,
                },
            "append_args":{
                "zarr_path":store_path,
                "station_var_keys":tuple(zip(*extract_station_vars))[1],
                "time_shard_size":262144,
                "time_chunk_size":65536,
                },
            } for p in src_years[yyyy]]
        with Pool(nworkers) as pool:
            for a,r in pool.imap_unordered(_mp_ghcnh_extract_and_append, args):
                print(f"got {a['extract_args']['psv_file'].name}")
        #f,t,x,s,q = extract_ghcn_psv(tmp_file)
