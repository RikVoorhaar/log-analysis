# %%
from log_parsing.parse_access_log import load_df_from_db
from log_parsing.database_def import TableNames
import polars as pl
import numpy as np
import matplotlib.pyplot as plt

df =  load_df_from_db(TableNames.PAGES_LOG)
df