from roi import external
from datetime import date
from roi import settings, utilities
import pandas as pd
import warnings

class BLS_Ops:
	def __init__(self):
		self.bls = external.BLS_API(query=False)
		self.cpi_adjustments = self.bls.cpi_adjustment_series
		self.employment_series = self.bls.bls_employment_series
		self.laborforce_series = self.bls.bls_laborforce_series
		self.wage_series = self.bls.bls_wage_series

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


class CPS_Ops:
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