# %%
'''
00:00 Intro
00:58 Government public data sets site
03:57 New project
04:30 Loading data from excel and initial discovery
13:46 Budget vs Year
36:34 Research by institution
48:40 Rising stars (Institutions with budget increase)
1:01:05 Unique words count
1:07:05 Budget vs Gender
1:13:46 Concluding words
'''

# %%
# ====================================================
# 04:30  Loading data from excel and initial discovery
# ====================================================

import pathlib
import warnings
import pandas as pd
warnings.filterwarnings('ignore')

file_name = "\\data\\-2012-2021-.-xlsx.xlsx"
relative_path = str(pathlib.Path().resolve())
research = pd.read_excel(relative_path + file_name)  # load into DataFrame object
# NOTE: unlike in jupyer, in *terminal* hebrew right-to-left is not supported in vscode (i.e. displayed in reverse)",
research.tail(n=2)


# %%
# without striping we find additional currency names, because some were entered
# with trailing spaces
research['מטבע'].str.strip().value_counts()

# %%
len(research['התכנית'].str.strip().value_counts())

# %%
# default sort is count descending
research['התכנית'].str.strip().value_counts()

# %%
# Plotting programs count with pandas
# -----------------------------------

# we'll use first 20
slice_ = research['התכנית'].str.strip().value_counts()[:20]  # this is now a Series object

# this plot will show hebrew with reversed text
slice_.plot(x='התכנית', kind='barh')  # barh for horizontal bars

# lets cheat by reversing the names in a copy of our series
slice_pretty = pd.Series({name[::-1]: count for name, count in slice_.iteritems()})
slice_pretty.plot(x='התכנית', kind='barh')


# %%
# ====================================================
# 13:46  Budget vs Year
# ====================================================

# see if Merkava number repeats self
research['מספר מרכבה'].str.strip().value_counts()

# see research details, filtered by Merkava number
# NOTE: another way to do it research.query() - but the query expr is messed
# up due to hebrew names and fails to parse correctly
research[research['מספר מרכבה'] == '3-15452'].head()

# lets mutate field names inplace in research (in R blog this was done ephemerally without changing original):
research_en = research.copy(deep=True)
research_en.rename(columns={'התכנית': 'program',
                            'שנה תקציבית': 'budget_year',
                            'תקציב ההסכם': 'budget',
                            'מוסד': 'institution'},
                   inplace=True)

# budget has string values as well, we need to dump these before we can continue
# errors='coerce': non-int string vals return NaN instead of original num, required for next ops like sum()
research_en['budget'] = pd.to_numeric(research_en['budget'], errors='coerce')

# already scales the Y values in the chart to 1e8
research_en.groupby('budget_year')['budget'].sum().astype(int).plot(kind='bar')

# NOTE 1: Another way to mutate is by adding fields as such:
# --------------
# research['program'] = research['']
# research['budget_year'] = research['שנה תקציבית']
# research['budget'] = pd.to_numeric(research['תקציב ההסכם'], errors='coerce'))
# research.head()
#
# NOTE 2: Yet another way to rename columns
# --------------
# col_names = research_en.columns.to_list()
# col_names[col_names.index('מוסד')] = 'institution'
# research_en.columns = col_names


# %%
# ====================================================
# 36:34  Research budget by institution
# ====================================================

# the following line results in a pandas.core.groupby.generic.DataFrameGroupBy
# object which is a list of tuples of 2 items - a tuple of the grouped_by values
# and a dataframe of the corresponding rows from the original dataframe:
#     research_en_grouped -> [((2012, 'אוניברסיטת בן גוריון בנגב'), df)]
# where the df is a dataframe consisting of all the rows from research_en of that
# budget_year and institution
research_en_grouped = research_en.groupby(['budget_year', 'institution'])
research_by_institution = research_en_grouped.sum().rename(columns={'budget': 'total_budget'})  # rename - dont overwrite budget with result
research_by_institution = research_by_institution.sort_values('total_budget', ascending=False)  # this is now a dataframe

# it seems the Technion appears in our index by 2 names: 'הטכניון' and 'הטכניון - מכון טכנולוגי לישראל'
# lets merge both instances of the index:
research_by_institution.index.names  # see multiindex levels, we want the 2nd one which is institution
index_map = {inst: 'הטכניון - מכון טכנולוגי לישראל' for inst in research_by_institution.index.get_level_values('institution')
             if 'טכניון' in inst}
research_by_institution.rename(inplace=True, level='institution', index=index_map)

# lets get top funded institutions, we'll sum accross the year, for each year.
# we achieve this by regrouping by insititution, dropping the year - and summing
top_funded_institutions = research_by_institution.groupby('institution').sum().sort_values('total_budget', ascending=False)
top_funded_institutions.head()

# lets clean up our data frame by taking only column we care about and top 8
# the index holds the institution names
top_funded_institutions = top_funded_institutions[['total_budget']].iloc[:8,:]

# filter research_by_institution (which has budget_year data as one of its index levels)
# by querying the 'institution' part of the index with the names of the top_funded_institutions
# NOTE: @ notation is used to dereference python vars within the query string
top_research_by_institution = research_by_institution.query('institution in @top_funded_institutions.index.values')
top_research_by_institution.head(10)


# %%
# Plotting our research budget per year
# -------------------------------------

# line plot - multi plots
# -----------------------

# simplify by dropping the index (convert data to columns instead), sort
df = top_research_by_institution.copy().reset_index().sort_values('budget_year')

# the following will print a line chart - but a separate for each institution group
inst_groups = df.groupby('institution')
# for inst in inst_groups.groups.keys():
#     inst_groups.get_group(inst).plot(kind='line',
#                                      x="budget_year",
#                                      y="total_budget",
#                                      title=inst[::-1])  # [::-1 invert hebrew text]


# %%
# line plot - sub plots
# ---------------------

import numpy as np
import matplotlib.pyplot as plt

ncols = 2
fig, ax = plt.subplots(figsize=(16,12),
                       sharey=True,
                       ncols=ncols,
                       nrows=int(np.ceil(inst_groups.ngroups/ncols)))


for i, (inst, grp) in enumerate(inst_groups):
    ax.flatten()[i].plot(grp['budget_year'], grp['total_budget'])
    ax.flatten()[i].set_title(inst[::-1])

fig.tight_layout()
plt.show()


# %%
# line plot continued - on same graph
# -----------------------------------

import matplotlib.pyplot as plt

# our dataframe top_research_by_institution is just a table with numerical
# index and everything else is in columns. the data is sorted by total_budget
# descending
df = top_research_by_institution.copy().reset_index().sort_values('budget_year')

# we can print in one line but we cant set different labels for lines like this
fig, ax = plt.subplots(figsize=(16,12))
df.groupby('institution').plot(kind='line', x="budget_year", y="total_budget", title=inst[::-1], ax=ax)

# %%
# line plot continued - on same graph
# -----------------------------------

# lets print them all on the same graph
fig, ax = plt.subplots(figsize=(16,12))
inst_groups = df.groupby('institution')
for inst, group in inst_groups:
    group.plot(kind='line',
               x="budget_year",
               y="total_budget",
               label=inst[::-1],    # [::-1 invert hebrew text]
               title='תקציב לשנה )מיליון ש"ח('[::-1], ax=ax)

ax.set_xlabel('Year')
ax.set_ylabel('Total Budget')
ax.legend(loc='best')
plt.show()

# %%
# bars plot - sub plots
# ---------------------

import numpy as np
import matplotlib.pyplot as plt

ncols = 2
fig, ax = plt.subplots(figsize=(16,12),
                       sharey=True,
                       ncols=ncols,
                       nrows=int(np.ceil(inst_groups.ngroups/ncols)))


for i, (inst, grp) in enumerate(inst_groups):
    ax.flatten()[i].bar(grp['budget_year'], grp['total_budget'])  # '.plot -> .bar'  is the only change from line sub plots
    ax.flatten()[i].set_title(inst[::-1])

fig.tight_layout()
plt.show()

# %%
# ======================================================
# 48:40 Rising stars (Institutions with budget increase)
# ======================================================

# lets dump a couple of empty columns, and save into research
#rising_stars = research_en.drop(columns=['Unnamed: 16', 'Unnamed: 17'], errors='ignore')  # ignore if already removed

# add a column to our mutated research_en (which is just reserach with some
# columns renamed to english)
rising_stars = research_en.copy()
rising_stars['year_fct'] = \
    rising_stars.apply(lambda row: 'yr19_21' if row['budget_year'] >= 2019 else 'yr12_18', axis=1)
rising_stars = rising_stars.drop(columns=['מספר סידורי', 'budget_year', 'Unnamed: 16', 'Unnamed: 17'], errors='ignore')  # ignore if already removed

rising_stars_grouped = rising_stars.groupby(['institution', 'year_fct'])
rising_stars_grouped = rising_stars_grouped.sum().rename(columns={'budget': 'total_budget'}).reset_index()

rising_stars = rising_stars_grouped.pivot_table(index=['institution'],
                                                columns=['year_fct'],
                                                values=['total_budget'],
                                                fill_value=0)
rising_stars = rising_stars['total_budget']
rising_stars['diff'] = rising_stars.apply(lambda row: (row['yr19_21']/3)/(row['yr12_18']/7), axis=1)  # divide by n year in interval

# drop institutions which only had funding in one of the groups
rising_stars = rising_stars[rising_stars['diff'] != np.inf]
rising_stars = rising_stars[rising_stars['diff'] != 0]

# this is what we want to plot, but its hebrew is wrong, so lets reverse the strings
institute_to_diff_heb = \
    pd.Series({inst[::-1]: diff for inst, diff in rising_stars.sort_values('diff')['diff'].iteritems()})

# plot with intercept
institute_to_diff_heb.plot(kind='barh', x='diff', figsize=(16,12)).axvline(x=1, color='black')


# %%
# ======================================================
# 1:01:05 Unique words count
# ======================================================

research_subj = research_en.rename(columns={'נושא': 'subject',
                                            'מספר סידורי': 'row'})
# split values by spaces - replaces strings with array of words
research_subj['subject'] = research_subj.subject.str.strip()
research_subj['subject'] = research_subj.subject.str.split()
# explode array or words into rows for each word in array, keep interesting columns
research_subj = research_subj.explode('subject')[['row', 'subject']]
research_subj.subject.value_counts()[:20,]

# %%
# ======================================================
# 1:07:05 Budget vs Gender
# ======================================================

research_en.rename(columns={'התכנית': 'program',
                            'שנה תקציבית': 'budget_year',
                            'תקציב ההסכם': 'budget',
                            'מגדר': 'gender'},
                   inplace=True)

research_en['budget'] = pd.to_numeric(research_en['budget'], errors='coerce')
research_en_grouped = research_en.groupby(['budget_year', 'gender'])
research_by_gender = research_en_grouped.sum().rename(columns={'budget': 'total_budget'})  # rename - dont overwrite budget with result

research_by_gender = research_by_gender.reset_index()[['budget_year', 'gender', 'total_budget']]

# the following gives us a nice plot but the bars are not normalized to 1 like in the blog
research_by_gender.pivot_table(
    index='budget_year', columns=['gender']).plot(
    kind='bar', stacked=True, figsize=(12, 8), color=['royalblue', 'palevioletred'])


# %%
# bars plot - normalized
# ----------------------

# there is no nice way to normalize like in R (seen in the blog video) for this
# kind of plot with pandas, so we'll calc percentage and plot that

research_by_gender_percent = \
    (research_by_gender.groupby(['budget_year', 'gender'])['total_budget'].sum()/research_by_gender.groupby(['budget_year'])['total_budget'].sum())

research_by_gender_percent.reset_index().pivot_table(
    index='budget_year', columns=['gender']).plot(
    kind='bar', stacked=True, figsize=(12,8), color=['royalblue', 'palevioletred'])
