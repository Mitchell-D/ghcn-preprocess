"""
------------------------------
Variable   Columns   Type
------------------------------
ID            1-11   Character
LATITUDE     13-20   Real
LONGITUDE    22-30   Real
ELEVATION    32-37   Real
STATE        39-40   Character
NAME         42-71   Character
GSN FLAG     73-75   Character
HCN/CRN FLAG 77-79   Character
WMO ID       81-85   Character
------------------------------
"""
from pathlib import Path
import numpy as np
import json

if __name__=="__main__":
    stations_path = Path(
        "/discover/nobackup/mtdodson/GHCNd/ghcnd-stations.txt")
    out_json_path = Path(
        "/discover/nobackup/mtdodson/GHCNd/ghcnd-stations.json")
    slines = [l.replace("\n","") for l in stations_path.open("r").readlines()]

    stations = {}
    for sl in slines:
        sid = sl[0:11].strip()
        stations[sid] = {
            "lat": float(sl[12:20].strip()),
            "lon": float(sl[21:30].strip()),
            "elev": float(sl[31:37].strip()),
            "state": sl[38:40].strip(),
            "name": sl[41:71].strip(),
            "gsn_flag": sl[72:75].strip(),
            "hcn_crn_flag": sl[76:79].strip(),
            "wmo": sl[80:85].strip(),
            }
    json.dump(stations, out_json_path.open("w"), indent=2)
