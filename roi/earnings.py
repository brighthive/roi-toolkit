import pandas as pd
import numpy as np
from datetime import date
from roi import settings
from roi import macrostats
from roi import get_data
import statsmodels.api as sm
import statsmodels.formula.api as smf
from os import path

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

class Summary(object):
	def __init__(self, frame_, earnings_column):
		self.frame_ = frame_
		self.earnings_column = earnings_column
		return(None)

	def earnings_summaries(self, grouping_factors):
		grouped = self.frame_.groupby(grouping_factors, as_index=False)[self.earnings_column].agg({'n':np.size,'mean':np.mean, 'median':np.median, 'sd':np.std})
		return(grouped)


class Premium(object):
	"""
	REDO DOCS HERE
	"""
	def __init__(self, mean_wages_file="data/mean_wages.csv", hs_mean_wages_file="data/hs_grads_mean_wages.csv", mincer_params_file = "data/mincer_params.pickle"):
		self.base_year = date.today().year - 1

		# Read in data and params that are packaged with the module
		self.all_mean_wages = get_data.all_mean_wages()
		self.hs_grads_mean_wages = get_data.hs_grads_mean_wages()
		self.mincer_params = get_data.mincer_params()

		# fetch CPI adjustments from the Bureay of Labor Statistics
		self.cpi_adjustments = get_data.cpi_adjustments()
		#BLS_API.get_cpi_adjustment_range(self.base_year - 19, self.base_year) # need to be connected to the internet to fetch BLS data

		# DELETE
		#self.cpi_adjustment_factor = 1.5341408621736492#BLS_API.get_cpi_adjustment(1999,self.base_year) # CPS data is converted into 1999 base, and then (below) we convert it into present-year dollars

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


	def mincer_based_wage_change(self, state, prior_education, current_age, starting_wage, years_passed):
		"""
		Given a state, a prior education level (CPS EDUC code), the current age of an individual, their wage
		before entering an educational program, and the time they spent in the program, this function calculates
		their counterfactual wage change, e.g. it calculates what their expected current wage would be if they had
		not participated in the program.

		It achieves this by using the relevant coefficients from the modified Mincer model fit in fit_mincer_model() above,
		which approximate the value of an additional year of work experience given prior education and existing years
		of work experience.

		Parameters:
		-----------
		prior_education : int
			Integer code describing individuals' prior education level
			# see https://cps.ipums.org/cps-action/variables/EDUC#codes_section

		current_age : int
			Individuals' current age (post program)

		starting_wage : float
			Individuals' annual wage prior to starting educational program

		years_passed : int
			Program length, e.g. 2 years for an associate's degree

		Returns
		-------
		float: the expected counterfactual wage change for an individual over the time they were in a program, in present-year dollars.

		"""
		schooling_coef = self.mincer_params['years_of_schooling']
		schooling_x_exp_coef = self.mincer_params['years_of_schooling:work_experience']
		exp_coef = self.mincer_params['work_experience']
		exp2_coef = self.mincer_params['np.power(work_experience, 2)']
		years_of_schooling = pd.cut([prior_education], bins=[0, 60, 73, 81, 92, 111, 123, 124, 125], right=True, labels=[10,12,14,13,16,18,19,20]).astype(int)[0] # this is a hack to get years of schooling; using the pandas function here for symmetry

		# get values for calculation
		work_experience_current = current_age - years_of_schooling - 6 # based on Heckman
		work_experience_start = work_experience_current - years_passed

		# calculate
		# change in natural log is approximately equal to percentage change
		value_start = schooling_x_exp_coef*work_experience_start*years_of_schooling + exp_coef*work_experience_start + exp2_coef*(work_experience_start**2)
		value_end = schooling_x_exp_coef*work_experience_current*years_of_schooling + exp_coef*work_experience_current + exp2_coef*(work_experience_current**2)
		
		# results
		percentage_wage_change = value_end - value_start
		counterfactual_current_wage = starting_wage * (1+percentage_wage_change)
		counterfactual_wage_growth = counterfactual_current_wage - starting_wage

		return(counterfactual_wage_growth)


if __name__ == "__main__":

	premium = Premium()

	example_frame = pd.DataFrame([{"age_group":'26-34',"year_start":2010,"year_end":2014,"statefip":30},{"age_group":'19-25',"year_start":2010,"year_end":2014,"statefip":1},{"age_group":'26-34',"year_start":2009,"year_end":2011,"statefip":2},{"age_group":'26-34',"year_start":2014,"year_end":2019,"statefip":30}])

	#example_frames_to_merge['adjusted'] = premium.adjust_to_current_dollars(example_frames_to_merge, 'column', cpi_adjustments = self.cpi_adjustments)

	wage_change_example = premium.wage_change_across_years(2009,2012,'26-34',1)
	wage_change_frame_example = premium.frames_wage_change_across_years(example_frame,'year_start','year_end','age_group','statefip')
	print(wage_change_frame_example)
	exit()


