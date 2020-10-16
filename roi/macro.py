from roi import external
from datetime import date
from roi import settings, utilities
import pandas as pd

class CPS:
	def __init__(self):
		return(None)

class BLS:
	def __init__(self):
		bls = BLS_API()

	def adjust_to_current_dollars(frame_, year_column_name, value_column_name, cpi_adjustments):
		max_year_row = cpi_adjustments.loc[cpi_adjustments['year'] == cpi_adjustments['year'].max()].iloc[0] # get latest year of CPI data
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
		frame_merged = frame_.merge(cpi_adjustments, left_on=year_column_name, right_on='year', how='left', indicator=True)

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


class ADI:
	def __init__(self):
		return(None)


class Calculations:
	"""
	Functions that take in dataframes produced by the BLS API and calculate statistics that will feed into ROI metrics.

	Methods
	-------
	employment_change(bls_employment_table, start_month, start_year, end_month, end_year)
		Returns the change in employment in between two month/year pairs

	wage_change(bls_wage_table, start_month, start_year, end_month, end_year)
		Returns the change in employment in between two month/year pairs
	"""

	# FIX
	def cpi_adjust_frame(self, frame_, wage_column, wage_year_column, year=date.today().year):
		"""
		This adjusts all wages to the current year's wages by default (though it will do whatever you tell it to!)
		It takes a frame and returns the original frame with the adjusted wages and the adjustment factors used.

		Parameters:
		-----------
		frame_ : Pandas DataFrame
			A DataFrame containing a wage column and a year column

		wage_column : str
			Name of the column containing the wage amounts to be adjusted. This column should be numeric; otherwise an error will arise.

		wage_year_column: str
			Name of the column containing the years associated with each wage. This column should be numeric; otherwise an error will arise.

		year : int
			The year to which all wages are to be adjusted, as in 1999 dollars or 2020 dollars, etc. Present year by default assuming you computer clock is correct.

		Returns:
		-------
		Original dataframe with "adjusted_wage" columns and "adjustment_factor" columns (self-explanatory).

		"""
		adjustment_frame = self.get_cpi_adjustment_range(year - 20, year)
		current_year_cpi = adjustment_frame.loc[adjustment_frame.year == year, 'cpi'].iat[0]
		adjusted_frame = frame_.merge(adjustment_frame, left_on=wage_year_column, right_on='year', how='left')
		adjusted_frame['adjustment_factor'] = current_year_cpi/cpi
		adjusted_frame['adjusted_wage'] = adjusted_frame['adjustment_factor'] * adjusted_frame[wage_column]
		return adjusted_frame

	def employment_change(bls_employment_table, bls_labor_force_table, state_code, start_month, end_month):
		"""
		This function takes year/month YYYY-MM as datetime arguments to avoid false precision.
		It fetches the associated figures from the BLS statistics provided as a function argument for
		the first of the month provided.

		BLS APIs return monthly data

		Parameters:
		-----------
		bls_employment_table : Pandas DataFrame
			Employment numbers for a given state over an arbitrary range of dates

		bls_labor_force_table : Pandas DataFrame
			Labor force numbers for a given state over an arbitrary range of dates

		start_month : str
			Format: "YYYY-MM"
			Start year and month of the period over which we want to identify % employment change

		end_month : str
			Format: "YYYY-MM"
			End year and month of the period over which we want to identify % employment change

		Returns
		-------
		A single number indicating the employment change over the given period
		"""

		bls_employment_table = bls_employment_table[bls_employment_table['state_code'] == state_code]
		bls_labor_force_table = bls_labor_force_table[bls_labor_force_table['state_code'] == state_code]

		# configure dtype of input
		start_month_year = pd.to_datetime(start_month).strftime("%Y-%m")
		end_month_year = pd.to_datetime(end_month).strftime("%Y-%m")

		# get employment figures
		start_employment = bls_employment_table.loc[bls_employment_table.month_year == start_month_year, 'value'].astype(int).iat[0]
		end_employment = bls_employment_table.loc[bls_employment_table.month_year == end_month_year, 'value'].astype(int).iat[0]

		# get labor force figures
		start_labor_force = bls_labor_force_table.loc[bls_labor_force_table.month_year == start_month_year, 'value'].astype(int).iat[0]
		end_labor_force = bls_labor_force_table.loc[bls_labor_force_table.month_year == end_month_year, 'value'].astype(int).iat[0]

		# calculation
		employment_change = float((end_employment / end_labor_force) - (start_employment / start_labor_force))

		return employment_change

	def wage_change(bls_wage_table, state_code, start_month, end_month):
		"""

		Parameters:
		-----------
		bls_wage_table : Pandas DataFrame
			Wage numbers for a given state over an arbitrary range of dates. Unadjusted!

		start_month : str
			Format: "YYYY-MM"
			Start year and month of the period over which we want to identify $ wage change

		end_month : str
			Format: "YYYY-MM"
			End year and month of the period over which we want to identify $ wage change

		Returns
		-------
		A single number indicating the wage change over the given period
		"""

		bls_wage_table = bls_wage_table[bls_wage_table['state_code'] == state_code]

		bls_wage_table['bls_annual_wages'] = bls_wage_table['value'] * 52 # weekly wage to annual

		# configure dtype of input
		start_month_year = pd.to_datetime(start_month).strftime("%Y-%m")
		end_month_year = pd.to_datetime(end_month).strftime("%Y-%m")

		# get wage figures
		start_wage = bls_wage_table.loc[bls_wage_table.month_year == start_month_year, 'value'].astype(float).iat[0]
		end_wage = bls_wage_table.loc[bls_wage_table.month_year == end_month_year, 'value'].astype(float).iat[0]

		# calculation
		wage_change = end_wage - start_wage

		return wage_change



class Macro_Comparison:
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