# %%
"""NOw let's try to do some geolocation shizzle"""

import os
import shutil
import tarfile
import urllib.request
from pathlib import Path

import geoip2.database
from dotenv import load_dotenv

from database_def import TableNames
import polars as pl
from load_log import load_df_from_db

load_dotenv()
GEOIP_LICENSE_KEY = os.getenv("GEOIP_LICENSE_KEY")

GEODB_URL = (
    "https://download.maxmind.com/app/geoip_download?edition_id"
    f"=GeoLite2-Country&license_key={GEOIP_LICENSE_KEY}&suffix=tar.gz"
)
DATABASE_FOLDER = Path("data")
DATABASE_FOLDER.mkdir(exist_ok=True)
GEODATABASE_PATH = DATABASE_FOLDER / "GeoLite2-Country.mmdb"


def download_geolitedate(skip_if_exist=True):
    if GEODATABASE_PATH.exists() and skip_if_exist:
        return

    ftpstream = urllib.request.urlopen(GEODB_URL)
    tarball_file = tarfile.open(fileobj=ftpstream, mode="r|gz")
    tarball_file.extractall(DATABASE_FOLDER)
    geolite_path = next(DATABASE_FOLDER.glob("GeoLite2*"))
    geolite_db_path = next(geolite_path.glob("*.mmdb"))
    geolite_db_path.rename(GEODATABASE_PATH)
    shutil.rmtree(geolite_path)


download_geolitedate()
# %%
pages_df = load_df_from_db(TableNames.PAGES_LOG)

# %%
addr_db = pages_df["http_x_forwarded_for"].value_counts()
remap = {"http_x_forwarded_for": "addr"}
addr_db.columns = [remap.get(c, c) for c in addr_db.columns]
with geoip2.database.Reader(GEODATABASE_PATH) as reader:

    def get_country(addr: str) -> str:
        response = reader.country(addr)
        name = response.country.name
        if name is None:
            return "unknown"
        return name

    addr_db = addr_db.with_columns(pl.col("addr").apply(get_country).alias("country"))
addr_db

# %%
country_counts = addr_db.groupby("country").agg(
    pl.sum("counts").alias("total"),
)
country_counts.sort(by=pl.col("total"), descending=True)
