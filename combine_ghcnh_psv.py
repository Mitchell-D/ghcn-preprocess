from pathlib import Path
import json
import multiprocessing as mp

def mp_combine_station(args):
    return args,combine_station(**args)

def combine_station(station_id, years, paths, lat_bounds, lon_bounds, out_dir,
        keep_fields=None):
    """
    """
    ys,ps = zip(*list(sorted(zip(years, paths), key=lambda v:v[0])))
    y0,yf = ys[0],ys[-1]
    ## make sure all years in the range are present
    expected_years = tuple(range(y0, yf+1))
    '''
    if not ys == expected_years:
        print(
            f"missing years: {sid}",
            sorted(list(set(expected_years) - set(ys)))
            )
        #continue
    '''
    full_header = None
    header = None
    keep_ixs = None
    all_lines = []
    for fp in ps:
        flines = [l.replace("\n", "") for l in fp.open("r").readlines()]
        tmph = flines.pop(0)

        ## make sure the header is the same for all files
        skip_station = False
        if header is None:
            ## skip stations that are outside the coordinate bounds
            fields = tmph.split("|")
            ix_lat = fields.index("LATITUDE")
            ix_lon = fields.index("LONGITUDE")
            tmpl = flines[0].split("|")
            cur_lat = float(tmpl[ix_lat])
            cur_lon = float(tmpl[ix_lon])
            if not (lat_bounds[0] < cur_lat < lat_bounds[1]):
                skip_station = True
                break
            if not (lon_bounds[0] < cur_lon < lon_bounds[1]):
                skip_station = True
                break
            full_header = tmph
            if not keep_fields is None:
                keep_ixs = []
                for f in keep_fields:
                    try:
                        keep_ixs.append(fields.index(f))
                    except:
                        raise ValueError(f"Feature not found: {f}\n", fields)
                header = "|".join([
                    v for i,v in enumerate(fields)
                    if i in keep_ixs
                    ])
            else:
                header = tmph
            all_lines.append(header)
        else:
            assert full_header == tmph
        if keep_ixs is None:
            all_lines += flines
        else:
            for i,fl in enumerate(flines):
                newfl = "|".join([
                    v for i,v in enumerate(fl.split("|"))
                    if i in keep_ixs
                    ])
                all_lines.append(newfl)
    if not skip_station:
        out_path = out_dir.joinpath(f"GHCNh_{station_id}_{y0}-{yf}.psv")
        out_path.open("w").write("\n".join(all_lines) + "\n")


if __name__=="__main__":
    psv_dir = Path("/discover/nobackup/projects/sport/GHCN/psv-hourly")
    out_dir = Path("/discover/nobackup/mtdodson/GHCNh/psv-combined")
    psv_paths = [p for p in psv_dir.iterdir() if p.suffix==".psv"]

    lat_bounds = (7, 72)
    lon_bounds = (-169, -52)
    nworkers = 12

    #keep_fields = json.load("ghcn_hourly_keep_fields.json")
    keep_fields = None

    stations = {}
    for p in psv_paths:
        _,*sid,yyyy = p.stem.split("_")
        if len(sid) > 1:
            sid = "-".join(sid)
        else:
            sid = sid[0]
        if not sid in stations.keys():
            stations[sid] = []
        stations[sid].append((int(yyyy), p))

    args = []
    for sid in stations.keys():
        ys,ps = zip(*list(sorted(stations[sid], key=lambda v:v[0])))
        args.append({
            "station_id":sid,
            "years":ys,
            "paths":ps,
            "lat_bounds":lat_bounds,
            "lon_bounds":lon_bounds,
            "out_dir":out_dir,
            "keep_fields":keep_fields,
            })

    with mp.Pool(nworkers) as pool:
        for a,r in pool.imap_unordered(mp_combine_station, args):
            print(f"processed {a['station_id']}")
            pass
