import pandas as pd
import numpy as np
from datetime import date
from . import settings
from .macrostats import BLS_API
#from macrostats import BLS_API
#import settings

"""
TO do here:

- mean wages for all
- mean wages for employed
- use person weights
- account for inflation?
- ???

"""

pd.set_option('display.float_format', lambda x: '%.3f' % x)


CPS_Education_Levels = [("GED",73),("BA",111),("MA",123),("PHD",125)]


class CPS_Ops(object):
	"""
	On init, this object reads in a CPS extract, calculates mean wages by age group across the whole population and for those whose
	highest level of education his high school, and sets properties of the class to dataframes with those contents.

	The class also offers functions for using this data to calculate average wage change across years, both given a single data point and
	given a data given multiple time periods, age groups, etc.
	"""
	def __init__(self):
		self.base_year = date.today().year - 1
		self.microdata = pd.read_csv(settings.File_Locations.cps_extract)
		self.microdata['age_group'] = pd.cut(self.microdata['AGE'], bins=[0,18,25,34,54,64,150], right=True, labels=['18 and under','19-25','26-34','35-54','55-64','65+']).astype(str)
		self.microdata['hs_education_at_most'] = self.microdata['EDUC'] < 80
		self.microdata.loc[self.microdata.INCWAGE > 9999998, 'INCWAGE'] = np.nan
		self.cpi_adjustment_factor = BLS_API.get_cpi_adjustment(1999,self.base_year) # CPS data is converted into 1999 base, and then (below) we convert it into present-year dollars
		self.microdata['INCWAGE_99'] = self.microdata['INCWAGE'] * self.microdata['CPI99'] * self.cpi_adjustment_factor
		self.hs_grads_only = self.microdata[self.microdata.hs_education_at_most == 1]
		self.get_all_mean_wages()
		self.get_hs_grads_mean_wages()

	def get_all_mean_wages(self):
		# Return a dataframe containing mean wages by year, state and age group
		mean_wages = self.microdata.groupby(['YEAR','STATEFIP','age_group']).apply(lambda x: pd.Series({"mean_INCWAGE":np.sum(x['INCWAGE_99'] * x['ASECWT'])/np.sum(x['ASECWT'])})).reset_index()
		self.all_mean_wages = mean_wages
		return None

	def get_hs_grads_mean_wages(self):
		# Return a dataframe containing mean wages for high school graduates (maximum ed) by year, state and age group
		mean_wages = self.hs_grads_only.groupby(['YEAR','STATEFIP','age_group']).apply(lambda x: pd.Series({"mean_INCWAGE":np.sum(x['INCWAGE_99'] * x['ASECWT'])/np.sum(x['ASECWT'])})).reset_index()
		self.hs_grads_mean_wages = mean_wages
		return None

	def get_mean_wage_by_ed_level(self, prereq_educ_level, program_educ_level, statefip):
		"""
		Calculate mean wages for individuals in a given state who are above a certain education level but below another one. Currently calculated for 2019 only.

		Reference:
		-----------
		CPS education codes

		Parameters:
		-----------
		prereq_educ_level : str
			CPS education recode code for the lower-bound education level

		program_educ_level : str
			CPS education recode code for the upper-bound education level

		statefip : str
			End year and month of the period over which we want to identify $ wage change

		Returns
		-------
		A single number indicating the mean wage across the dataset for this group of people.
		"""
		max_ed = self.microdata[(self.microdata.EDUC >= prereq_educ_level) & (self.microdata.EDUC < program_educ_level) & (self.microdata.STATEFIP == statefip) & (self.microdata.YEAR == 2019)]
		mean_wage = np.sum(max_ed["INCWAGE_99"] * max_ed["ASECWT"]) / np.sum(max_ed["ASECWT"])
		return(mean_wage)

	def wage_change_across_years(self, start_year, end_year, age_group_at_start, statefip):
		"""
		Calculate mean wage change across years for individuals in a given state and age group.

		Parameters:
		-----------
		start_year : int
			CPS education recode code for the lower-bound education level

		end_year : int
			CPS education recode code for the upper-bound education level

		age_group_at_start : str
			One of ['18 and under','19-25','26-34','35-54','55-64','65+']. These are divvied up in the CPS data at init of the CPS_Ops object.

		statefip : str
			State FIPS code, e.g. "08"

		Returns
		-------
		A single number indicating the mean wage across the dataset for this group of people.
		"""
		wage_start = self.all_mean_wages.loc[(self.all_mean_wages['YEAR'] == start_year) & (self.all_mean_wages['age_group'] == age_group_at_start) & (self.all_mean_wages['STATEFIP'] == statefip), 'mean_INCWAGE'].iat[0]
		wage_end = self.all_mean_wages.loc[(self.all_mean_wages['YEAR'] == end_year) & (self.all_mean_wages['age_group'] == age_group_at_start) & (self.all_mean_wages['STATEFIP'] == statefip), 'mean_INCWAGE'].iat[0]
		wage_change = wage_end - wage_start
		return(wage_change)

	def frames_wage_change_across_years(self, ind_frame, start_year_column, end_year_column, age_group_start_column, statefip_column, hsgrads_only = True):
		"""
		Given a dataframe with individual microdata, add a new column describing the change in state-level wages
		for people in their age group across the provided time frame (e.g. time spent in educational/training program).

		Parameters:
		-----------
		ind_frame : Pandas DataFrame
			Dataframe containing microdata for individuals

		start_year_column : str
			Name of column containing individuals' years of entry into educational programs

		end_year_column : str
			Name of column containing individuals' years of exit from educational programs

		age_group_start_column : str
			Name of column containing age groups.
			These are in ['18 and under','19-25','26-34','35-54','55-64','65+'].

		statefip_column : str
			Name of column contianing state FIPS codes

		hsgrads_only : boolean
			If true, we correct for macro trends using only data from high school graduates (max education)

		Returns
		-------
		A dataframe containing a new column ("wage_change") which expresses the difference between pre- and post-program earnings corrected for trend.
		"""
		if (hsgrads_only == False):
			cps_frame = self.all_mean_wages
		else:
			cps_frame = self.hs_grads_mean_wages
		merged_start = ind_frame.merge(cps_frame, left_on=[start_year_column, age_group_start_column, statefip_column], right_on=['YEAR','age_group','STATEFIP'], how='left')
		merged_both = merged_start.merge(cps_frame, left_on=[end_year_column, age_group_start_column, statefip_column], right_on=['YEAR','age_group','STATEFIP'], how='left', suffixes=('_start','_end'))
		merged_both['wage_change'] = merged_both['mean_INCWAGE_end'] - merged_both['mean_INCWAGE_start']
		return(merged_both)

	def hsgrad_wage_projections(self):
		return None

if __name__ == "__main__":
	
	cps = CPS_Ops()

	hs_wages = cps.get_mean_wage_by_ed_level(73, 111, 8)
	ba_wages = cps.get_mean_wage_by_ed_level(111, 123, 8)
	print(hs_wages)
	print(ba_wages)
	exit()

	example_frames_to_merge = pd.DataFrame([{"age_group":'26-34',"year_start":2010,"year_end":2014,"statefip":30},{"age_group":'19-25',"year_start":2010,"year_end":2014,"statefip":1},{"age_group":'26-34',"year_start":2009,"year_end":2011,"statefip":2},{"age_group":'26-34',"year_start":2014,"year_end":2019,"statefip":30}])
	wage_change_example = cps.wage_change_across_years(2009,2012,'26-34',1)
	wage_change_frame_example = cps.frames_wage_change_across_years(example_frames_to_merge,'year_start','year_end','age_group','statefip')
	print(wage_change_frame_example)
	exit()

