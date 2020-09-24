from roi import utilities

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