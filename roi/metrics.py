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
	def group_average_premiums(self, grouping_variable):
		data = self.data
		data['earnings_premium'] = self.full_premium
		summaries = utilities.multiple_describe(data, grouping_variable, 'earnings_premium')
		# here - do not report if less than default number!
		return(summaries)


class Employment_Likelihood:
	def __init__(self, dataframe, program_identifier, entry_year_month, exit_year_month, employed_at_end, employed_at_start, age_group_at_start, state):
		self.raw_likelihood_at_end = self._raw_likelihood_at_end(dataframe, program_identifier, employed_at_end)
		self.raw_likelihood_change = self._raw_likelihood_change(dataframe, program_identifier, employed_at_end, employed_at_start)
		self.data = dataframe
		self.macro_correction = self._fetch_macro_correction(dataframe, entry_year_month, exit_year_month, state, query)
		self.employment_premium_individual = self._calculate_employment_premium(dataframe[employed_at_end], dataframe[employed_at_start])
		self.employment_premium = self._full_employment_premium(dataframe, program_identifier, self.employment_premium_individual)

	def _raw_likelihood_at_end(self, dataframe, program_identifier, employed_at_end):
		raw = utilities.Summaries.summary_by_group(dataframe, program_identifier, employed_at_end)
		return(raw)

	def _raw_likelihood_change(self, dataframe, program_identifier, employed_at_end, employed_at_start):
		individual_emp_difference = dataframe[employed_at_end] - dataframe[employed_at_start]
		dataframe['empchange'] = individual_emp_difference
		change = utilities.Summaries.summary_by_group(dataframe, program_identifier, 'empchange')
		return(change)

	@staticmethod
	def _fetch_macro_correction(dataframe, entry_year_month, exit_year_month, state, query):
		rates = utilities.Local_Data.bls_employment_series()
		dataframe[state] = utilities.check_state_code_series(dataframe[state])
		entry_employment = dataframe.merge(rates, left_on=[state, entry_year_month], right_on=['state_code','month_year'], how='left')
		exit_employment = dataframe.merge(rates, left_on=[state, exit_year_month], right_on=['state_code','month_year'], how='left')
		return(entry_employment['employment_rate'] - exit_employment['employment_rate'])

	def _calculate_employment_premium(self, employed_at_end, employed_at_start):
		return(employed_at_end - employed_at_start - self.macro_correction)

	@staticmethod
	def _full_employment_premium(dataframe, program_identifier, individual_premium):
		dataframe['emp_premium'] = individual_premium
		full = utilities.Summaries.summary_by_group(dataframe, program_identifier, 'emp_premium').rename(columns={"mean":"mean_employment_premium"})
		return(full)

class Completion:
	def __init__(self, dataframe, program_identifier, entry_year, exit_year, completion_indicator):
		self.data = dataframe
		self.completion_rates = self._completion_rates(dataframe, program_identifier, completion_indicator)
		self.time_to_completion = self._time_to_completion(dataframe, program_identifier, entry_year, exit_year, completion_indicator)

	def _time_to_completion(self, data, program_identifier, entry_year, exit_year, completion_indicator):
		completers_only = data[data[completion_indicator] == 1]
		data['time_to_completion'] = data[exit_year] - data[entry_year]
		aggregated = utilities.Summaries.summary_by_group(data, program_identifier, 'time_to_completion')
		return(aggregated)

	def _completion_rates(self, data, program_identifier, completion_indicator):
		aggregated = utilities.Summaries.summary_by_group(data, program_identifier, completion_indicator)
		return(aggregated)
