import tarfile
from pathlib import Path
from multiprocessing import Pool

def mp_extract_tar_gz(args):
    return args,extract_tar_gz(**args)

def extract_tar_gz(src_path:Path, extract_dir:Path):
    with tarfile.open(src_path, "r:gz") as tb:
        tb.extractall(path=extract_dir.as_posix())
    src_path.unlink()

if __name__=="__main__":
    source_dir = Path("/discover/nobackup/mtdodson/GHCNh/source")
    #extract_dir = Path("/discover/nobackup/mtdodson/GHCNh/psv")
    extract_dir = Path("/discover/nobackup/projects/sport/GHCN/psv-hourly")
    nworkers = 13
    source_paths = [
        #"ghcn-hourly_v1.1.0_d2001_c20260707.tar.gz",
        #"ghcn-hourly_v1.1.0_d2002_c20260707.tar.gz",
        #"ghcn-hourly_v1.1.0_d2003_c20260707.tar.gz",
        #"ghcn-hourly_v1.1.0_d2004_c20260707.tar.gz",
        #"ghcn-hourly_v1.1.0_d2005_c20260707.tar.gz",
        #"ghcn-hourly_v1.1.0_d2006_c20260707.tar.gz",
        #"ghcn-hourly_v1.1.0_d2007_c20260707.tar.gz",
        #"ghcn-hourly_v1.1.0_d2008_c20260707.tar.gz",
        #"ghcn-hourly_v1.1.0_d2009_c20260707.tar.gz",
        #"ghcn-hourly_v1.1.0_d2010_c20260707.tar.gz",
        #"ghcn-hourly_v1.1.0_d2011_c20260707.tar.gz",
        #"ghcn-hourly_v1.1.0_d2012_c20260707.tar.gz",
        "ghcn-hourly_v1.1.0_d2013_c20260707.tar.gz",
        "ghcn-hourly_v1.1.0_d2014_c20260707.tar.gz",
        "ghcn-hourly_v1.1.0_d2015_c20260707.tar.gz",
        "ghcn-hourly_v1.1.0_d2016_c20260707.tar.gz",
        "ghcn-hourly_v1.1.0_d2017_c20260707.tar.gz",
        "ghcn-hourly_v1.1.0_d2018_c20260707.tar.gz",
        "ghcn-hourly_v1.1.0_d2019_c20260707.tar.gz",
        "ghcn-hourly_v1.1.0_d2020_c20260707.tar.gz",
        "ghcn-hourly_v1.1.0_d2021_c20260707.tar.gz",
        "ghcn-hourly_v1.1.0_d2022_c20260707.tar.gz",
        "ghcn-hourly_v1.1.0_d2023_c20260707.tar.gz",
        "ghcn-hourly_v1.1.0_d2024_c20260707.tar.gz",
        "ghcn-hourly_v1.1.0_d2025_c20260707.tar.gz",
        ]
    args = [
        {"src_path":source_dir.joinpath(p), "extract_dir":extract_dir}
        for p in source_paths
        ]
    with Pool(nworkers) as pool:
        for a,_ in pool.imap_unordered(mp_extract_tar_gz, args):
            print(f"extracted {a['src_path'].name}")
