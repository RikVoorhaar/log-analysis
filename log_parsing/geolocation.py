# %%
"""NOw let's try to do some geolocation shizzle"""

import os
import shutil
import tarfile
import urllib.request


import geoip2.database
import polars as pl
from dotenv import load_dotenv

from log_parsing.config import PROJECT_ROOT, logger

load_dotenv()
GEOIP_LICENSE_KEY = os.getenv("GEOIP_LICENSE_KEY")

GEODB_URL = (
    "https://download.maxmind.com/app/geoip_download?edition_id"
    f"=GeoLite2-Country&license_key={GEOIP_LICENSE_KEY}&suffix=tar.gz"
)
DATABASE_FOLDER = PROJECT_ROOT / "data"
DATABASE_FOLDER.mkdir(exist_ok=True)
GEODATABASE_PATH = DATABASE_FOLDER / "GeoLite2-Country.mmdb"


def download_geolitedate(skip_if_exist=True):
    if GEODATABASE_PATH.exists() and skip_if_exist:
        logger.info("Geolite database already downloaded. Skipping download.")
        return

    logger.info("Downloading geolite database.")
    ftpstream = urllib.request.urlopen(GEODB_URL)
    tarball_file = tarfile.open(fileobj=ftpstream, mode="r|gz")
    tarball_file.extractall(DATABASE_FOLDER)
    geolite_path = next(DATABASE_FOLDER.glob("GeoLite2*"))
    geolite_db_path = next(geolite_path.glob("*.mmdb"))
    geolite_db_path.rename(GEODATABASE_PATH)
    shutil.rmtree(geolite_path)
    logger.info("Geolite database downloaded.")


download_geolitedate()


def get_country_info(addr: pl.Series) -> pl.Series:
    logger.info(f"Getting country info for {len(addr)} addresses.")
    with geoip2.database.Reader(GEODATABASE_PATH) as reader:

        def get_country(addr: str) -> str:
            response = reader.country(addr)
            name = response.country.name
            if name is None:
                return "unknown"
            return name

        res = addr.apply(get_country).alias("country")
    return res


# pages_df = load_df_from_db(TableNames.PAGES_LOG)
# pages_df
# addr_db = pages_df["http_x_forwarded_for"].value_counts()
# remap = {"http_x_forwarded_for": "addr"}
# addr_db.columns = [remap.get(c, c) for c in addr_db.columns]
# addr_db.with_columns(pl.col("addr").map(get_country_info))
# country_counts = addr_db.groupby("country").agg(
#     pl.sum("counts").alias("total"),
# )
# country_counts.sort(by=pl.col("total"), descending=True)
