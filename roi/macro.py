from roi import external
from datetime import date
from roi import settings, utilities
import pandas as pd
import warnings

class BLS_Ops:
	"""

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
		end_CPI = self.cpi_adjustments.loc[self.cpi_adjustments['year'] == end_year, 'cpi'].iloc[0] # get latest year of CPI data
		start_CPI = self.cpi_adjustments.loc[self.cpi_adjustments['year'] == start_year, 'cpi'].iloc[0] # get latest year of CPI data
		return(end_CPI / start_CPI)


	def employment_change(self, state_code, start_month, end_month):
		"""
		This function takes year/month YYYY-MM as datetime arguments to avoid false precision.
		It fetches the associated figures from the BLS statistics provided as a function argument for
		the first of the month provided.

		BLS APIs return monthly data

		Parameters:
		-----------


		Returns
		-------
		A single number indicating the employment change over the given period
		"""

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

		Parameters:
		-----------


		Returns
		-------
		A single number indicating the wage change over the given period
		"""

		temp_frame = pd.DataFrame({'start_month':start_month,'end_month':end_month,'state_code':state_code})

		# employment merges
		temp_frame['wage_start'] = temp_frame.merge(self.wage_series, left_on=['start_month','state_code'], right_on=['month_year','state_code'], how='left')['value']
		temp_frame['wage_end'] = temp_frame.merge(self.wage_series, left_on=['end_month','state_code'], right_on=['month_year','state_code'], how='left')['value']

		if convert == True:
			temp_frame['start_year'] = temp_frame['start_month'].str.split('-',expand=True)[0].astype(int)
			temp_frame['end_year'] = temp_frame['end_month'].str.split('-',expand=True)[0].astype(int)
			wage_start = self.adjust_to_current_dollars(temp_frame, 'start_year', 'wage_start')
			wage_end = self.adjust_to_current_dollars(temp_frame, 'end_year', 'wage_end')
		else:
			wage_start = temp_frame['wage_start']
			wage_end = temp_frame['wage_end']

		wage_change = (wage_end - wage_start)*52 # convert to annual wage
		return(wage_change)


class ADI:
	def __init__(self):
		return(None)