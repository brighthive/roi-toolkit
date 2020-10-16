import pandas as pd
import numpy as np
from datetime import date
from roi import settings
from roi import external
from roi import utilities
from roi.utilities import Local_Data
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

class Earnings_Premium:
	def __init__(self, frame, state, prior_education, wage_at_start, wage_at_end, program_start_year, program_end_year, age):

		# get external data necessary for calculation
		self.mincer_params = Local_Data.mincer_params()
		self.hs_grads_mean_wages = Local_Data.hs_grads_mean_wages()

		# pile input data into class properties
		self.data = frame
		self.state = frame[state] # HERE - check for fip and format!
		self.prior_education = frame[prior_education]
		self.program_start_year = frame[program_start_year]
		self.program_end_year = frame[program_end_year]
		self.wage_at_start = frame[wage_at_start]
		self.wage_at_end = frame[wage_at_end]
		self.current_age = frame[age]

		# conduct calculations
		self.years_in_program = self.program_end_year - self.program_start_year
		self.predicted_wage = self.mincer_predicted_wage(self.state, self.prior_education, self.current_age, self.wage_at_start, self.years_in_program)
		self.full_premium = self.wage_at_end - self.predicted_wage

	def mincer_predicted_wage(self, state, prior_education, current_age, starting_wage, years_passed):

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
		years_of_schooling = pd.cut(prior_education, bins=[-1, 60, 73, 81, 92, 111, 123, 124, 125], right=True, labels=[10,12,14,13,16,18,19,20]).astype(float) # this is a hack to get years of schooling; using the pandas function here for symmetry

		# get values for calculation
		work_experience_current = current_age - years_of_schooling - 6 # based on Heckman
		work_experience_start = work_experience_current - years_passed

		# if starting wage is not given for high school graduates, give them the mean high school wage
		# do this for 18-25 year-old HS grads ONLY! This is defensible on the grounds that these individuals
		# are just entering the labor force and are broadly similar to each other. The assumption is less defensible
		# for older unemployed workers with high school degrees, who likely differ systematically from older EMPLOYED
		# workers with high school degrees.
		hs_mergeframe = pd.DataFrame(prior_education)
		hs_mergeframe['state'] = state
		hs_mergeframe['age_group'] = utilities.age_to_group(current_age - years_passed)
		hs_mergeframe['entry_year'] = 2009

		hs_merged = hs_mergeframe.merge(self.hs_grads_mean_wages, left_on=['state','age_group', 'entry_year'], right_on=['STATEFIP','age_group','YEAR'], how='left')
		hsgrad_wages = hs_merged['mean_INCWAGE']

		# replace!
		starting_wage.loc[(current_age <= 25) & (pd.isna(starting_wage))] = hsgrad_wages.loc[(current_age <= 25) & (pd.isna(starting_wage))]

		# deal with other missing wages

		# calculate
		# change in natural log is approximately equal to percentage change
		value_start = schooling_x_exp_coef*work_experience_start*years_of_schooling + exp_coef*work_experience_start + exp2_coef*(work_experience_start**2)
		value_end = schooling_x_exp_coef*work_experience_current*years_of_schooling + exp_coef*work_experience_current + exp2_coef*(work_experience_current**2)

		# results
		percentage_wage_change = value_end - value_start
		counterfactual_current_wage = starting_wage * (1+percentage_wage_change)

		return(counterfactual_current_wage)


	# eliminate this???
	def Group_Earnings_Premium(self, grouping_variable):
		data = self.data
		data['earnings_premium'] = self.full_premium
		summaries = utilities.multiple_describe(data, grouping_variable, 'earnings_premium')
		# here - do not report if less than default number!
		return(summaries)

class Macro_Changes():
	def __init__(self):
		return(None)


class Comparison:
	def __init__(self):
		self.base_year = date.today().year - 1

		# Read in data and params that are packaged with the module
		self.all_mean_wages = Local_Data.all_mean_wages()
		self.hs_grads_mean_wages = Local_Data.hs_grads_mean_wages() # mean wages for high school graduates in every state

		self.cpi_adjustments = Local_Data.cpi_adjustments() # CPI adjustments from the Bureau of Labor Statistics

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

		# Validation
		if age_group_at_start not in settings.General.CPS_Age_Groups:
			raise ValueError("Invalid age group. Argument age_group_at_start must be in ['18 and under','19-25','26-34','35-54','55-64','65+']")
		else:
			pass

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
			Name of column containing state FIPS codes

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
		return(merged_both['wage_change'])


