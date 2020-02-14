	def get_wage_baselines(self, statefip):
		baselines = self.microdata[self.microdata.STATEFIP == statefip]

		# max ed level
		baselines['max_education_level'] = ""
		baselines.loc[(baselines.EDUC >= 73) & (baselines.EDUC < 91),"max_education_level"] = "GED"
		baselines.loc[(baselines.EDUC >= 111) & (baselines.EDUC < 123),"max_education_level"] = "BA"
		baselines.loc[(baselines.EDUC >= 123) & (baselines.EDUC < 124),"max_education_level"] = "MA"

		# year intervals
		baselines["year_interval"] = np.nan
		baselines.loc[baselines.YEAR == self.base_year, "year_interval"] = 10
		baselines.loc[baselines.YEAR == self.base_year - 5, "year_interval"] = 5
		baselines.loc[baselines.YEAR == self.base_year - 9, "year_interval"] = 1
		baselines.loc[baselines.YEAR == self.base_year - 10, "year_interval"] = 0

		# mean wage by year and education level
		#grouped_by_year = baselines.groupby(['year_interval','max_education_level']).apply(lambda x: pd.Series({"mean_INCWAGE":np.sum(x['INCWAGE_99'] * x['ASECWT'])/np.sum(x['ASECWT'])})).reset_index()

		# median wage by year and education level
		grouped_by_year = baselines.groupby(['year_interval','max_education_level']).apply(lambda x: pd.Series({"meanie": self.weighted_median(x, 'INCWAGE_99','ASECWT'), "n": len(x)})).reset_index()

		return(grouped_by_year)

	def weighted_median(self, dataframe, value_name, weight):
		dataframe = dataframe[pd.notna(dataframe[value_name])]
		sorted_ = dataframe.sort_values(by = value_name)
		sorted_['weight_sum'] = sorted_[weight].cumsum()
		sorted_['weight_sum_shift1'] = sorted_['weight_sum'].shift(1)
		median_weightsum = np.max(sorted_['weight_sum']) / 2
		median_value = sorted_.loc[(sorted_['weight_sum'] >= median_weightsum) & (sorted_['weight_sum_shift1'] <= median_weightsum), value_name].iat[0]
		return(median_value)