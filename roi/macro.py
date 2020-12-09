from datetime import date
from roi import settings, utilities
import pandas as pd
import warnings


"""
This submodule contains methods and classes for working with macroeconomic data and using it to conduct basic calculations.
As of this writing (09/12/2020), BLS_Ops() is the only class in the submodule, but it does many useful things!
"""

class BLS_Ops:
	"""
	On init, this class reads in previously prepared data that should be packaged with the ROI Toolkit.
	In order to refresh this data and store it locally (in the directories where e.g. this class will look for it),
	analysts or engineers can and should use the BLS_API.fetch_bls_data() method after signing up for a free
	key for the U.S. Bureau of Labor Statistics API.

	On init, if this data is available, BLS_Ops() will load up historical employment, wage, labor force, and inflation data.

	"""
	def __init__(self):
		try:
			self.cpi_adjustments = utilities.Local_Data.cpi_adjustments()
			self.employment_series = utilities.Local_Data.bls_employment_series()
			self.laborforce_series = utilities.Local_Data.bls_laborforce_series()
			self.wage_series = utilities.Local_Data.bls_wage_series()
			self.max_cpi_year = self.cpi_adjustments['year'].max()
		except Exception as E:
			print("The ROI Toolkit is packaged with precalculated BLS series at the state level, but BLS_Ops() couldn't load at least one of these files:{}\n".format(E))

	def adjust_to_current_dollars(self, frame_, year_column_name, value_column_name):
		"""
		Given a dataframe with a year column and a column of values, this method will adjust all values to present-year dollars.
		Present year is defined as the latest year of available CPI indices in the data packaged with the ROI Toolkit.

		Parameters:
			frame_              :   A pandas DataFrame
			year_column_name    :   The name of the column in frame_ that contains years
			value_column_name   :   The name of the column in frame_ that contains values

		Returns:
			adjusted_column     :   A pandas Series containing CPI-adjusted values of value_column_name

		"""
		max_year_row = self.cpi_adjustments.loc[self.cpi_adjustments['year'] == self.cpi_adjustments['year'].max()].iloc[0] # get latest year of CPI data
		max_year = max_year_row['year']
		max_cpi_index = max_year_row['cpi']

		print("Latest CPI year in provided BLS data is {}: All dollars being adjusted to {} dollars.".format(str(max_year), str(max_year)))

		# Error checking and warnings
		value_nas = pd.isna(frame_[value_column_name]).sum()
		year_nas = pd.isna(frame_[year_column_name]).sum()

		if value_nas > 0:
			warnings.warn("Value column {} contains {} NA values ({}%) of total.".format(value_column_name, value_nas, round(100*value_nas/len(frame_),2)))

		if year_nas > 0:
			warnings.warn("Year column {} contains {} NA values ({}%) of total.".format(value_column_name, value_nas, round(100*year_nas/len(frame_),2)))

		# Merge provided frame with CPI data
		frame_merged = frame_.merge(self.cpi_adjustments, left_on=year_column_name, right_on='year', how='left', indicator=True)

		# Report years that didn't merge
		unmerged_from_frame = frame_merged[frame_merged['_merge'] == "left_only"]
		unmerged_len = len(unmerged_from_frame)

		if unmerged_len > 0:
			warnings.warn("{} rows in column {} could not be merged with provided CPI data. Please note that (1) the BLS API provides only up to 20 years of data; if you want to use more, you will have to manually combine multiple queries. (2) We do not recommend using more than ten years of historical data in calculations.".format(unmerged_len, year_column_name))
			print("Years in provided dataframe for which there is no data in the provided CPI frame:\n")
			print(set(frame_merged.loc[frame_merged['_merge'] == "left_only", year_column_name]))

		# adjust and return
		adjusted_column = frame_merged[value_column_name]/frame_merged['cpi'] * max_cpi_index
		return(adjusted_column)

	def get_single_year_adjustment_factor(self, start_year, end_year):
		"""
		Provides the adjustment factor required in order to convert dollar values from start_year to dollar_values from end_year.
		For example, if the factor is 1.5, then $100 in start_year is equivalent to $150 in end-year.

		Parameters:
			start_year          :   Year FROM which the analyst is converting - YYYY numeric scalar
			end_year            :   Year TO which the analyst is converting - YYYY numeric scalar

		Returns:
			adjustment_factor   :   A scalar adjustment factor allowing conversion for inflation

		"""

		# validation
		if not isinstance(start_year, int) or not isinstance(end_year, int):
			if isinstance(start_year, pd.Series) or isinstance(end_year, pd.Series):
				print("To convert a Pandas Series using CPI, use the adjust_to_current_dollars() method.")
			raise ValueError("start_year and end_year must be scalar integers")

		end_CPI = self.cpi_adjustments.loc[self.cpi_adjustments['year'] == end_year, 'cpi'].iloc[0] # get latest year of CPI data
		start_CPI = self.cpi_adjustments.loc[self.cpi_adjustments['year'] == start_year, 'cpi'].iloc[0] # get latest year of CPI data
		adjustment_factor = end_CPI / start_CPI
		return(adjustment_factor)

	def employment_change(self, frame_, state_code_column_name, start_month_column_name, end_month_column_name):
		"""
		This method takes a dataframe and three column names. Each row in the provided dataframe should correspond
		to a unique individual. The idea of this function is to, for each individual, provide the overall change
		in the employment rate in the state and over the time period provided.

		This function takes year/month YYYY-MM as datetime arguments to avoid false precision. So, for example,
		a row might have the state as "AK", start_month as "2010-10" and end_month as "2012-05. For this individual,
		the function will return the change in the overall employment rate in Alaska over the provided time period.

		The idea here is to provide a way of simply quickly correcting for macroeconomic changes. If the employment rate
		for graduates of a program is 95% after they graduated, and if only 90% were employed prior to entry, a naive comparison
		might suggest that the program increases odds of employment by 5 percentage points. However, if the average change in employment
		over these individuals' periods of participation was an increase in 10%, then you might conclude that the program is actually
		hurting their chances of employment by reducing them 5 percentage points.

		Please note that this is itself a naive reading: employment figures are calculated for the population at large, and program
		participants are not likely to be a representative subsample. However, correcting for macroeconomic trends in this way is
		an important first step in interpreting data about program completers.

		Please note as well that the employment rate here is given, as is typical with conventional calculations of the UNEMPLOYMENT
		rate, as a percentage of the total labor force, not of the working-age population at large.

		Parameters:
			frame_                        :   A pandas dataframe containing one row per individual
			state_code_column_name        :   The name of a column containing two-character state codes, e.g. "CO"
			start_month_column_name       :   The name of a column containing start months of format "YYYY-MM"
			end_month_column_name         :   The name of a column containing end months of format "YYYY-MM"

		Returns:
			percent_employed_change       :   A pandas series describing the change in the overall employment rate in the location and over the time period listed for each individual in the dataset
		"""

		state_code = frame_[state_code_column_name]
		start_month = frame_[start_month_column_name]
		end_month = frame_[end_month_column_name]

		# check state codes
		all_state_codes = state_code.unique()
		unmerged_state_codes = set(all_state_codes).difference(set(utilities.Data.state_crosswalk.keys()))
		if len(unmerged_state_codes) > 0:
			warnings.warn("Series passed as argument state_code contains invalid values for state codes. Please refer to https://www.bls.gov/respondents/mwr/electronic-data-interchange/appendix-d-usps-state-abbreviations-and-fips-codes.htm for valid codes.")

		# do the work
		temp_frame = pd.DataFrame({'start_month':start_month,'end_month':end_month,'state_code':state_code})

		# employment merges
		employment_start_merged = temp_frame.merge(self.employment_series, left_on=['start_month','state_code'], right_on=['month_year','state_code'], how='left')['value']
		employment_end_merged = temp_frame.merge(self.employment_series, left_on=['end_month','state_code'], right_on=['month_year','state_code'], how='left')['value']

		# laborforce merges
		lf_start_merged = temp_frame.merge(self.laborforce_series, left_on=['start_month','state_code'], right_on=['month_year','state_code'], how='left')['value']
		lf_end_merged = temp_frame.merge(self.laborforce_series, left_on=['end_month','state_code'], right_on=['month_year','state_code'], how='left')['value']

		percent_employed_change = (employment_end_merged/lf_end_merged) - (employment_start_merged/lf_start_merged)

		return(percent_employed_change)

	def wage_change(self, state_code, start_month, end_month, convert=False):
		"""
		This method takes a dataframe and three column names. Each row in the provided dataframe should correspond
		to a unique individual. The idea of this function is to, for each individual, provide the overall change
		in the average wage in the state and over the time period provided.

		This function takes year/month YYYY-MM as datetime arguments to avoid false precision. So, for example,
		a row might have the state as "AK", start_month as "2010-10" and end_month as "2012-05. For this individual,
		the function will return the change in the overall employment rate in Alaska over the provided time period.

		The idea here is to provide a way of simply quickly correcting for macroeconomic changes. If the average wage
		for graduates of a program is $50k after they graduated, and if the average ewage was $45k prior to entry, a naive comparison
		might suggest that the program increases odds of employment by $5k. However, if the average wage change over
		these individuals' periods of participation was an increase in $10k, then you might conclude that the program is actually
		hurting their earnings by approximately $5k.

		Please note that this is itself a naive reading: employment figures are calculated for the population at large, and program
		participants are not likely to be a representative subsample. However, correcting for macroeconomic trends in this way is
		an important first step in interpreting data about program completers.

		Please note as well that this method uses a "naive" method for calculating annual wages, taking weekly BLS wage data and multiplying by 52.

		Parameters:
			frame_                        :   A pandas dataframe containing one row per individual
			state_code_column_name        :   The name of a column containing two-character state codes, e.g. "CO"
			start_month_column_name       :   The name of a column containing start months of format "YYYY-MM"
			end_month_column_name         :   The name of a column containing end months of format "YYYY-MM"

		Returns:
			wage_change       :   A pandas series describing the change in the overall wage cjange in the location and over the time period listed for each individual in the dataset
		"""

		state_code = frame_[state_code_column_name]
		start_month = frame_[start_month_column_name]
		end_month = frame_[end_month_column_name]

		# check state codes
		all_state_codes = state_code.unique()
		unmerged_state_codes = set(all_state_codes).difference(set(utilities.Data.state_crosswalk.keys()))
		if len(unmerged_state_codes) > 0:
			warnings.warn("Series passed as argument state_code contains invalid values for state codes. Please refer to https://www.bls.gov/respondents/mwr/electronic-data-interchange/appendix-d-usps-state-abbreviations-and-fips-codes.htm for valid codes.")

		temp_frame = pd.DataFrame({'start_month':start_month,'end_month':end_month,'state_code':state_code})

		# employment merges
		temp_frame['wage_start'] = temp_frame.merge(self.wage_series, left_on=['start_month','state_code'], right_on=['month_year','state_code'], how='left')['value']
		temp_frame['wage_end'] = temp_frame.merge(self.wage_series, left_on=['end_month','state_code'], right_on=['month_year','state_code'], how='left')['value']

		# convert to current dollars
		if convert == True:
			temp_frame['start_year'] = temp_frame['start_month'].str.split('-',expand=True)[0].astype(int)
			temp_frame['end_year'] = temp_frame['end_month'].str.split('-',expand=True)[0].astype(int)
			wage_start = self.adjust_to_current_dollars(temp_frame, 'start_year', 'wage_start')
			wage_end = self.adjust_to_current_dollars(temp_frame, 'end_year', 'wage_end')
		else: # or not
			wage_start = temp_frame['wage_start']
			wage_end = temp_frame['wage_end']

		wage_change = (wage_end - wage_start)*52 # convert to annual wage
		return(wage_change)
