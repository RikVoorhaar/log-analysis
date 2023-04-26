
Everything sees to work now. Here's a todo:
<!-- - Add plot titles -->
<!-- - Make filters apear above graph; not next to graph -->
<!-- - Make filters a floating element, perhaps in a collapsible thing -->
<!-- - Improve layout; now it's horendous -->
<!-- - Page popularity plot breaks when we have a single page only -->
<!-- - Updating daterange doesn't trigger the update -->
- We need to add a feedback for when a filter is empty
<!-- - Delete button should be a cross -->
<!-- - Add filter button should be moved, and maybe look nicer -->
<!-- - Colors need to be consistent; each filter has an index, and color should be tied to index. We should be able to see the color in a preview in the filter row. This also means that we can remove the label in the plots; we just number them.  -->
<!-- - add colors to filter list -->
<!-- - Make it impossible to delete the last filter -->
<!-- - add logging and timing -->
<!-- - The date plot seems to be missing the first/last couple days -->




Plots to try:
- Country breakdowns for page / date range
- Relative ranking of pages
- Time of day breakdown; both in UTC time and converted to local timezone (is this in country dataset?)
- Distrubution of repeat vists
- Make in dashboard easy way to filter data by: page, date range, country


So plan:
<!-- - Make filter functions that return filtered version of pages_df -->
<!-- - Add timezone info / local time into data -->
<!-- - Make script for rebuilding the dataset; this should take all logs from /parsed and put them back into the queue, then it should backup + delete the database, and recompute all the tables. -->
- Parse filtered pages_df into plot data
- Make callbacks for the interesting plot data
- Make nice outline

It would be nice if it's easy to compare two different filter settings. E.g., make it
easy to compare what happens for a specific country, and then also for two countries,
or all countries. 

Perhaps this is ambitious for now, but it would be good to keep this functionality
in mind during development. 

Like, we want a user interface where we can click "add filter", and that produces another
row with dropdowns etc. 
Perhaps in that case it only makes sense to talk about geographic filters and page filters. 

This means that we should make an abstract `Filter` class, and pass a list of `Filters` 
together with the original dataframe to each function.


Now how do plot functions get created?
I think we can have a `plot_data` function that takes a single dataframe as input, and outputs a dataframe with two columns. Then there is a second function that translates
this into the actual plotly figure. 

I think it's actually best if we don't have a `Filter` class, but rather a `FilteredDataframe` class. This makes it easier to do the filtering once, and in the app
we can pass these to the plot callbacks using a global variable