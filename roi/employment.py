from roi import settings, utilities, macrostats

class Employment_Likelihood:
	def __init__(self, dataframe, program_identifier, entry_year_month, exit_year_month, employed_at_end, employed_at_start, age_group_at_start, state, query=False):
		if query == False:
			print("By default, the Employment_Likelihood class operates using an instance of the BLS_API() class with query = False")
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
		bls = macrostats.BLS_API(query=query)
		rates = bls.employment_rate_series
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
