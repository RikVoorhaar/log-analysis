# %%
import matplotlib.pyplot as plt
import pandas as pd
from log_parsing.database_def import create_engine_table
import numpy as np

engine, access_log = create_engine_table()
with engine.connect() as conn:
    stmt = access_log.select()
    df = pd.read_sql(stmt, conn)

# %%
%%time
first_day = df["time_iso8601"].dt.date.min()
days_since = df["time_iso8601"].dt.date - first_day
# days_since.value_counts().sort_index().plot()
# %%
weekday = df["time_iso8601"].dt.weekday
weekday.value_counts().sort_index().plot()
plt.xticks(np.arange(7), ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"])

# %%
df["connection"].value_counts().value_counts().sort_index().plot().set_yscale("log")
plt.ylabel("Number of requests")
plt.xlabel("Number of connections")
plt.show()

# %%


def compute_date_hour_count(df: pd.DataFrame) -> pd.DataFrame:
    date_hour = df["time_iso8601"].dt.floor("H")
    date_hour_count = date_hour.value_counts().sort_index()
    min_date = date_hour_count.index.min()
    max_date = date_hour_count.index.max()
    date_hour_count = date_hour_count.reindex(
        pd.date_range(min_date, max_date, freq="H")
    ).fillna(0)
    return date_hour_count


%time date_hour_count = compute_date_hour_count(df)

# %%
columns
# %%
def make_pages_df(df):
    mask = (df["request_uri"].str.endswith("/")) & (df["status"] == 200)
    df_pages = df[mask]
    referers = df_pages["request_uri"]
    referers = referers.str.extract(r"\/([^\/]+)\/?$").fillna('home')
    df_pages = df_pages[['time_iso8601','connection']]
    df_pages['hour'] = df_pages['time_iso8601'].dt.floor("H")
    df_pages['day'] = df_pages['hour'].dt.floor("D")
    df_pages['weekday'] = df_pages['day'].dt.weekday
    df_pages['page_name'] = referers
    return df_pages

%timeit pages_df = make_pages_df(df)
# %%
"""plenty of good ideas, but let's for now focus on things specific to each web page; 
We can make a couple simple plots, and benchmark how fast the data is to compute. 
"""


# %%
%%time
page_names_per_connection = pages_df.groupby('connection')['page_name'].nunique()
page_names_per_connection.value_counts() / page_names_per_connection.size
# %%

# %%
df['status'].value_counts()
# %%
# referers = referers.str.extract(r"\/([^\/]+)\/?$")
pd.value_counts(referers).to_clipboard()

# %%
plt.figure(figsize=(10, 5))
plt.ylabel("Number of requests")
plt.xlabel("Date")
date_hour_count.to_csv("date_hour_count.csv")

# %%
"""Actually just using pure request count doesn't make much sense, since different
webpages have different number of requests. We should filter by requests for actual
webpages first, I suppose. 

I guess we can filter by http_referrer, and just take those that come from my own website.
"""

# %%