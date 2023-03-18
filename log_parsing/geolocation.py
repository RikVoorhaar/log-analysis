# %%
"""NOw let's try to do some geolocation shizzle"""

import os
import shutil
import tarfile
from enum import Enum
import urllib.request


import geoip2.database
import polars as pl
from dotenv import load_dotenv

from log_parsing.config import PROJECT_ROOT, logger

load_dotenv()
GEOIP_LICENSE_KEY = os.getenv("GEOIP_LICENSE_KEY")

GEOLITE2_COUNTRY_URL = (
    "https://download.maxmind.com/app/geoip_download?edition_id"
    f"=GeoLite2-Country&license_key={GEOIP_LICENSE_KEY}&suffix=tar.gz"
)
GEOLITE2_CITY_URL = (
    "https://download.maxmind.com/app/geoip_download?edition_id"
    f"=GeoLite2-City&license_key={GEOIP_LICENSE_KEY}&suffix=tar.gz"
)
DATABASE_FOLDER = PROJECT_ROOT / "data"
DATABASE_FOLDER.mkdir(exist_ok=True)
GEOLITE2_COUNTRY_PATH = DATABASE_FOLDER / "GeoLite2-Country.mmdb"
GEOLITE2_CITY_PATH = DATABASE_FOLDER / "GeoLite2-City.mmdb"


class GeoliteDatabaseTypes(Enum):
    COUNTRY = "country"
    CITY = "city"


geolite_databases = {
    GeoliteDatabaseTypes.COUNTRY: (GEOLITE2_COUNTRY_URL, GEOLITE2_COUNTRY_PATH),
    GeoliteDatabaseTypes.CITY: (GEOLITE2_CITY_URL, GEOLITE2_CITY_PATH),
}


def download_geolitedate(
    database_type: GeoliteDatabaseTypes, skip_if_exist: bool = True
):
    url, path = geolite_databases[database_type]

    if path.exists() and skip_if_exist:
        logger.info("Geolite database already downloaded. Skipping download.")
        return

    logger.info("Downloading geolite database.")
    ftpstream = urllib.request.urlopen(url)
    tarball_file = tarfile.open(fileobj=ftpstream, mode="r|gz")
    tarball_file.extractall(DATABASE_FOLDER)
    geolite_path = next(DATABASE_FOLDER.glob("GeoLite2*"))
    geolite_db_path = next(geolite_path.glob("*.mmdb"))
    geolite_db_path.rename(path)
    shutil.rmtree(geolite_path)
    logger.info("Geolite database downloaded.")


download_geolitedate(GeoliteDatabaseTypes.CITY)


def get_geolite_reader(database_type: GeoliteDatabaseTypes) -> geoip2.database.Reader:
    _, path = geolite_databases[database_type]
    return geoip2.database.Reader(path)


def map_country_name(addr: pl.Series) -> pl.Series:
    logger.info(f"Getting country info for {len(addr)} addresses.")
    with get_geolite_reader(GeoliteDatabaseTypes.COUNTRY) as reader:

        def get_country(addr: str) -> str:
            response = reader.country(addr)
            name = response.country.name
            if name is None:
                return "unknown"
            return name

        res = addr.apply(get_country).alias("country")
    return res


def map_timezone(addr: pl.Series) -> pl.Series:
    with get_geolite_reader(GeoliteDatabaseTypes.CITY) as reader:

        def get_timezone(addr: str) -> str:
            response = reader.city(addr)
            timezone = response.location.time_zone
            if timezone is None:
                timezone = "UTC"
            return timezone

        timezones = addr.apply(get_timezone).alias("timezone")
    return timezones


def map_continent(addr: pl.Series) -> pl.Series:
    with get_geolite_reader(GeoliteDatabaseTypes.CITY) as reader:

        def get_continent(addr: str) -> str:
            response = reader.city(addr)
            continent = response.continent.name
            if continent is None:
                continent = "unknown"
            return continent

        continents = addr.apply(get_continent).alias("continent")
    return continents


def get_local_time(group_df: pl.DataFrame):
    tz = group_df["timezone"][0]

    return group_df.select(["request_id", "time"]).with_columns(
        (
            pl.col("time")
            .dt.replace_time_zone("UTC")
            .dt.convert_time_zone(tz)
            .dt.replace_time_zone(None)
        ).alias("local_time")
    )


def add_country_info(df: pl.DataFrame) -> pl.DataFrame:
    df = df.with_columns(
        pl.col("addr").map(map_timezone).alias("timezone"),
        pl.col("addr").map(map_country_name).alias("country"),
        pl.col("addr").map(map_continent).alias("continent"),
    )
    df_tz = df.groupby("timezone").apply(get_local_time).sort(by=pl.col("request_id"))
    df = df.sort(by=pl.col("request_id")).with_columns(df_tz["local_time"])
    return df
