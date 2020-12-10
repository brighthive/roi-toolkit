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
This submodule is home to return calculations -- the R in ROI.

Please note that the classes and methods contained in this submodule are just the start for rigorous and robust ROI measurement.
These methods allow an analyst of intermediate technical sophistication to calculate individual- and program-level outcome of various kinds,
to adjust for some common measurement concerns, and to produce summary statistics.

These methods DO NOT represent an avenue for exploring the causal impact of a given program or institution, for drawing determinate
conclusions about program efficacy, or for identifying what programs, institutions, or student groups need more or less funding.

Causal claims are the province of randomized experiments, quasi-random observational studies, and carefully done time series studies.
None of these avenues are supported here.

However, much can be done for learners and workers using non-causal statistical inference. For example, each of the methods in this
submodule calculates returns at the level of the individual student. An analyst can use the equity metrics introduced in equity.py
in order to identify whether and how returns may differ across student groups, to investigate the drivers of inequality, and explore
how some groups of students may be uniquely well- or poorly-served by a given program or institution.

"""

pd.set_option('display.float_format', lambda x: '%.3f' % x)

CPS_Education_Levels = [("GED",73),("BA",111),("MA",123),("PHD",125)]

class Earnings_Premium:
	"""
	This method calculates predicted (counterfactual) wages for students who have participated in education or training
	programs, calulates the difference between their observed and counterfactual wages, and produces program- or institution-level
	statistics summarizing the difference between observed and counterfactual wages, which can be interpreted as the
	putative impact of participating in the program.

	The method surveys.CPS_Ops().fit_mincer_model fits a Mincer model, using microdata to produce coefficients that are used in this method.
	These coefficients most be stored locally in order for this method to work. They are packaged with the module.

	Parameters:
		frame                :   A dataframe containing joined student education and wage data
		state                :   The name of a column in frame containing state FIPS codes as strings
		prior_education      :   The name of a column in frame containing students' prior education levels before program participation
		wage_at_start        :   The name of a column in frame containing students' earnings or wages at a set period (e.g. 1 quarter) before program entry
		wage_at_end          :   The name of a column in frame containing students' earnings or wages at a set period (e.g. 1 quarter) AFTER program entry
		program_start_year   :   The name of a numeric column (YYYY) containing the program start year
		program_end_year     :   The name of a numeric column (YYYY) containing the program end year
		age                  :   The name of a column containing students' CURRENT AGEs

	Attributes:
		The series associated with all parameters are set as attributes. In addition, we have...

		years_in_program     :   A Pandas series ordered in the same order as frame containing the number of years each student spent in their program
		predicted_wage       :   A pandas series ordered in the same order as frame containing students' predicted wages, based on a Mincer model trained on CPS data
		full_premium         :   A pandas series ordered in the same order as frame containing the differenc between students' predicted and actual wages, e.g. their earnings premium
	"""
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
		self.predicted_wage = self.mincer_predicted_wage(self.state, self.prior_education, self.current_age, self.wage_at_start, self.years_in_program, self.program_start_year)
		self.full_premium = self.wage_at_end - self.predicted_wage

	def mincer_predicted_wage(self, state, prior_education, current_age, starting_wage, years_passed, entry_year):
		"""
		Given a state, a prior education level (CPS EDUC code), the current age of an individual, their wage
		before entering an educational program, and the time they spent in the program, this function calculates
		their counterfactual wage change, e.g. it calculates what their expected current wage would be if they had
		not participated in the program.

		It achieves this by using the relevant coefficients from the modified Mincer model fit in fit_mincer_model() above,
		which approximate the value of an additional year of work experience given prior education and existing years
		of work experience.

		Parameters:
			prior_education              : int, pandas series, Integer code describing individuals' prior education level. see https://cps.ipums.org/cps-action/variables/EDUC#codes_section
			current_age                  : int, pandas series, Individuals' current age (post program)
			starting_wage                : float, pandas series, Individuals' annual wage prior to starting educational program
			years_passed                 : int, pandas series, Program length, e.g. 2 years for an associate's degree

		Returns:
			counterfactual_current_wage  : the expected counterfactual wage change for an individual over the time they were in a program, in present-year dollars.

		"""
		schooling_coef = self.mincer_params['years_of_schooling']
		schooling_x_exp_coef = self.mincer_params['years_of_schooling:work_experience']
		exp_coef = self.mincer_params['work_experience']
		exp2_coef = self.mincer_params['np.power(work_experience, 2)']
		years_of_schooling = pd.cut(prior_education, bins=[-1, 60, 73, 81, 92, 111, 123, 124, 125], right=True, labels=[10,12,14,13,16,18,19,20]).astype(float) # this is a hack to get years of schooling; using the pandas function here for symmetry

		# get values for calculation
		work_experience_current = current_age - years_of_schooling - 6 # based on Heckman's work
		work_experience_start = work_experience_current - years_passed

		"""
		If starting wage is not given for high school graduates, give them the mean high school wage.
		Do this for 18-25 year-old HS grads ONLY! This is defensible on the grounds that these individuals
		are just entering the labor force and are broadly similar to each other. The assumption is less defensible
		for older unemployed workers with high school degrees, who likely differ systematically from older EMPLOYED
		workers with high school degrees.
		"""
		hs_mergeframe = pd.DataFrame(prior_education)
		hs_mergeframe['state'] = state
		hs_mergeframe['age_group'] = utilities.age_to_group(current_age - years_passed)
		hs_mergeframe['entry_year'] = entry_year

		hs_merged = hs_mergeframe.merge(self.hs_grads_mean_wages, left_on=['state','age_group', 'entry_year'], right_on=['STATEFIP','age_group','YEAR'], how='left')
		hsgrad_wages = hs_merged['mean_INCWAGE']

		# replace!
		starting_wage.loc[(current_age <= 25) & (pd.isna(starting_wage))] = hsgrad_wages.loc[(current_age <= 25) & (pd.isna(starting_wage))]

		# change in natural log is approximately equal to percentage change
		value_start = schooling_x_exp_coef*work_experience_start*years_of_schooling + exp_coef*work_experience_start + exp2_coef*(work_experience_start**2)
		value_end = schooling_x_exp_coef*work_experience_current*years_of_schooling + exp_coef*work_experience_current + exp2_coef*(work_experience_current**2)

		# results
		percentage_wage_change = value_end - value_start
		counterfactual_current_wage = starting_wage * (1+percentage_wage_change)

		return(counterfactual_current_wage)

	def group_average_premiums(self, grouping_variable):
		"""
		This method calculates summary statistics about the earnings premium at the group level, for example the
		mean and median earnings premium at the program level. The mean, then, is braodly interpretable as the
		additional annual earnings a program participant can expect to earn. Quantiles and standard deviations
		are also calculated and returned.

		Parameters:
			grouping_variable : A varname or list of varnames across which to calculate summary stats

		Returns:
			summaries : A pandas dataframe containing the results of the summarization.
		"""
		data = self.data
		data['earnings_premium'] = self.full_premium
		summaries = utilities.multiple_describe(data, grouping_variable, 'earnings_premium')
		# here - do not report if less than default number!
		return(summaries)


class Employment_Likelihood:
	"""
	This class calculates calculates, at the individual and group level, the change in likelihood of employment associated with a given group
	(e.g. program or institution).

	Parameters:
		dataframe                       :  A pandas dataframe containing individual student data
		program_identifier              :  Column name for the column containing a pandas series constituting  unique identifier for programs (or institutions, or program/institution pairs)
		entry_year_month                :  Column name - Each student's program entry date, expressed as the string "YYYY-MM"
		exit_year_month                 :  Column name - Each student's program exit date, expressed as the string "YYYY-MM"
		employed_at_end                 :  Column name - Dummy variable denoting each student's employment status at program completion, 1 if employed, 0 otherwise
		employed_at_start               :  Column name - Dummy variable denoting each student's employment status at program start, 1 if employed, 0 otherwise
		state                           :  Colun name - Student state FIPS codes (string)

	Attributes:
		raw_likelihood_at_end           :  Summary statistics at the program level of a students' likelihood of employment on program completion
		raw_likelihood_change           :  Summary statistics at the program level of a students' CHANGE in likelihood of employment between program start and program end
		data                            :  The original dataframe passed to the class instance
		macro_correction                :  A pandas series with an entry for each student, ordered according to the original dataframe, containing the state-level employment change over the time they were in their program
		employment_premium_individual   :  Individual-level change in employment likelihood -- not easily interpretable at the individual level
		employment_premium              :  Summary statistics at the program level of a students' employment likelihood premium-- average change in employment over program length, corrected for trend
	"""
	def __init__(self, dataframe, program_identifier, entry_year_month, exit_year_month, employed_at_end, employed_at_start, state):
		self.raw_likelihood_at_end = self._raw_likelihood_at_end(dataframe, program_identifier, employed_at_end)
		self.raw_likelihood_change = self._raw_likelihood_change(dataframe, program_identifier, employed_at_end, employed_at_start)
		self.data = dataframe
		self.macro_correction = self._fetch_macro_correction(dataframe, entry_year_month, exit_year_month, state)
		self.employment_premium_individual = self._calculate_employment_premium(dataframe[employed_at_end], dataframe[employed_at_start])
		self.employment_premium = self._full_employment_premium(dataframe, program_identifier, self.employment_premium_individual)

	def _raw_likelihood_at_end(self, dataframe, program_identifier, employed_at_end):
		"""
		Parameters:
			dataframe           :  Dataframe with individual-level data
			program_identifier  :  Column name with unique program identifier
			employment_at_end   :  Column name with a 1/0 dummy denoting whether an individual is employed at program end

		Returns:
			raw                 :  A pandas dataframe containing group-level summary statistics describing likelihood of employment at program end

		"""
		raw = utilities.Summaries.summary_by_group(dataframe, program_identifier, employed_at_end)
		return(raw)

	def _raw_likelihood_change(self, dataframe, program_identifier, employed_at_end, employed_at_start):
		"""
		Parameters:
			dataframe           :  Dataframe with individual-level data
			program_identifier  :  Column name with unique program identifier
			employment_at_end   :  Column name with a 1/0 dummy denoting whether an individual is employed at program end
			employment_at_start :  Column name with a 1/0 dummy denoting whether an individual is employed on program start

		Returns:
			raw                 :  A pandas dataframe containing group-level summary statistics describing the CHANGE ikelihood of employment between program start and program end

		"""
		individual_emp_difference = dataframe[employed_at_end] - dataframe[employed_at_start]
		dataframe['empchange'] = individual_emp_difference
		change = utilities.Summaries.summary_by_group(dataframe, program_identifier, 'empchange')
		return(change)

	@staticmethod
	def _fetch_macro_correction(dataframe, entry_year_month, exit_year_month, state):
		"""
		Provides state-level change in employment rates for all provided states and time frames.

		Parameters:
			dataframe          : A pandas dataframe
			entry_year_month   : Name of a column containing a start date expressed as a string "YYYY-M"
			exit_year_month    : Name of a column containing an end date expressed as a string "YYYY-M"
			state              : Name of a column containing states expressed as FIPS codes e.g. "05" (string)

		Returns:
			correction         : A panda series of length len(dataframe) with state-level change in employment for the specified states and time frames

		"""
		rates = utilities.Local_Data.bls_employment_series()
		dataframe[state] = utilities.check_state_code_series(dataframe[state])
		entry_employment = dataframe.merge(rates, left_on=[state, entry_year_month], right_on=['state_code','month_year'], how='left')
		exit_employment = dataframe.merge(rates, left_on=[state, exit_year_month], right_on=['state_code','month_year'], how='left')
		correction = entry_employment['employment_rate'] - exit_employment['employment_rate']
		return(correction)

	def _calculate_employment_premium(self, employed_at_end, employed_at_start):
		"""
		Calculate employment premium at the individual level. The series this produces is not easily interpretable
		as a quantity in its own right and is mostly useful for the _full_employment_premium() method below.

		Parameters:
			employed_at_end    : a pandas series taking values 0 or 1, denoting employment at program completion
			employed_at_start  : a pandas series taking values 0 or 1, denoting employment at program start

		Returns:
			individual_premium : a pandas series denoting individual-level change in employment, corrected for macroeconomic trend.
		"""

		individual_premium = employed_at_end - employed_at_start - self.macro_correction
		return(individual_premium)

	@staticmethod
	def _full_employment_premium(dataframe, program_identifier, individual_premium):
		"""
		This is the main method in this class. It calculates the change in employment at the program level for all provided programs, corrected for trend.
		It produces, mean, median, standard deviation, and various quantiles.

		Parameters:
			dataframe           : a pandas datarame
			program_identifier  : name of a column containing unique program identifiers
			individual_premium  : a pandas series, ordered to align with dataframe, that contains individual employment likelihood premia

		Returns:
			full                : a pandas dataframe containing a summary of employment premia at the program level
		"""
		dataframe['emp_premium'] = individual_premium
		full = utilities.Summaries.summary_by_group(dataframe, program_identifier, 'emp_premium').rename(columns={"mean":"mean_employment_premium"})
		return(full)

class Completion:
	"""
	Statistics about program completion

	Parameters:
		dataframe            : a pandas dataframe containing individual student data
		program_identifier   : name of a column in dataframe containing unique program identifiers
		entry_year           : name of column in dataframe containing program entry years
		exit_year            : name of column in dataframe containing program exit years
		completion_indicator : name of column in dataframe containing a 1/0 dummy variable denoting whether students completed the program

	Attributes:
		data                 : the original dataframe passed
		completion_rates     : a pandas dataframe containing program-level summary statistics about completion rate per program
		time_to_completion   : a pandas dataframe containing program-level summary statistics about time to completion per program


	"""

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
