from roi import settings, utilities

class Employment_Likelihood:
	def __init__(self, dataframe, program_identifier, entry_year, exit_year, employed_at_end, employed_at_start, age_group_at_start):
		self.raw_likelihood_at_end = self._raw_likelihood_at_end(dataframe, program_identifier, employed_at_end)
		self.raw_likelihood_change = self._raw_likelihood_change(dataframe, program_identifier, employed_at_end, employed_at_start)
		return(None)

	def _raw_likelihood_at_end(self, dataframe, program_identifier, employed_at_end):
		raw = utilities.Summaries.summary_by_group(dataframe, program_identifier, employed_at_end)
		return(raw)

	def _raw_likelihood_change(self, dataframe, program_identifier, employed_at_end, employed_at_start):
		individual_emp_difference = dataframe[employed_at_end] - dataframe[employed_at_start]
		dataframe['empchange'] = individual_emp_difference
		change = utilities.Summaries.summary_by_group(dataframe, program_identifier, 'empchange')
		return(change)

	def _fetch_macro_correction():
		default_start_month = 9
		default_end_month = 6
		return(None)

	def _calculate_employment_premium():
		return(None)