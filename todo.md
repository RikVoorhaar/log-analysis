
Plots to try:
- Country breakdowns for page / date range
- Relative ranking of pages
- Time of day breakdown; both in UTC time and converted to local timezone (is this in country dataset?)
- Distrubution of repeat vists
- Make in dashboard easy way to filter data by: page, date range, country


So plan:
- Make filter functions that return filtered version of pages_df
- Add timezone info / local time into data
- Make script for rebuilding the dataset; this should take all logs from /parsed and put them back into the queue, then it should backup + delete the database, and recompute all the tables.
- Parse filtered pages_df into plot data
- Make callbacks for the interesting plot data
- Make nice outline