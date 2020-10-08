import numpy as np
import pandas as pd
import warnings
from pandas.api.types import is_numeric_dtype

class Data:
	state_crosswalk = {
		"AL":1,
		"AK":2,
		"AZ":4,
		"AR":5,
		"CA":6,
		"CO":8,
		"CT":9,
		"DE":10,
		"DC":11,
		"FL":12,
		"GA":13,
		"HI":15,
		"ID":16,
		"IL":17,
		"IN":18,
		"IA":19,
		"KS":20,
		"KY":21,
		"LA":22,
		"ME":23,
		"MD":24,
		"MA":25,
		"MI":26,
		"MN":27,
		"MS":28,
		"MO":29,
		"MT":30,
		"NE":31,
		"NV":32,
		"NH":33,
		"NJ":34,
		"NM":35,
		"NY":36,
		"NC":37,
		"ND":38,
		"OH":39,
		"OK":40,
		"OR":41,
		"PA":42,
		"PR":72,
		"RI":44,
		"SC":45,
		"SD":46,
		"TN":47,
		"TX":48,
		"UT":49,
		"VT":50,
		"VA":51,
		"VI":78,
		"WA":53,
		"WV":54
	}


class Summaries:

	def summary_by_group(frame_, grouping_factors, column_to_aggregate):
		grouped = frame_.groupby(grouping_factors, as_index=False)[column_to_aggregate].agg({'n':np.size,'mean':np.mean, 'median':np.median, 'sd':np.std, 'min':np.min, 'max':np.max})
		return(grouped)


class Dates:

	def combine(year_series, month_series):
		return(None)

	def separate(year_and_month_column):
		return(None)


def State_To_FIPS(state_abbreviation):
	crosswalk = Data.state_crosswalk
	# hardcoded - FIPS aren't changing anytime soon
	if state_abbreviation not in crosswalk.keys():
		raise ValueError("{} is not a valid state abbreviation. State_To_FIPS() requires an abbreviation like CA and is case-sensitive.".format(state_abbreviation))
	else:
		return(crosswalk[state_abbreviation])

	return(None)

def check_state_code(state_code):
	if not isinstance(state_code, str):
		warnings.warn("State codes, though integers, should be passed as strings. Something else was passed. Attempting to coerce to string.")
	else:
		pass
	try:
		state_code = str(state_code).zfill(2) # left pad with zeroes to align with FIP codes
		return(state_code)
	except Exception as e:
		print("Couldn't coerce state code to string: {}".format(e))
	return(None)

def check_state_code_series(state_code_series):
	if not isinstance(state_code_series, pd.Series):
		raise ValueError("check_state_code_series() takes a Pandas Series as an argument. Something else was passed.")
	else:
		pass

	if is_numeric_dtype(state_code_series):
		warnings.warn("State codes, though integers, should be passed as strings. Something else was passed. Attempting to coerce to string.")
	else:
		pass

	try:
		state_code_series = state_code_series.astype(str).str.pad(2, fillchar="0") # left pad with zeroes to align with FIP codes
		return(state_code_series)
	except Exception as e:
		print("Couldn't coerce state code to string: {}".format(e))
	return(None)


class Adjustments:

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

class Local_Data:
	def all_mean_wages():
		return(pd.read_csv(settings.File_Locations.mean_wages_location, converters={"state_code":utilities.check_state_code}))

	def hs_grads_mean_wages():
		return(pd.read_csv(settings.File_Locations.hs_mean_wages_location, converters={"STATEFIP":utilities.check_state_code}))

	def mincer_params():
		return(pd.read_pickle(settings.File_Locations.mincer_params_location))

	def cpi_adjustments():
		return(pd.read_csv(settings.File_Locations.cpi_adjustments_location))

	def bls_employment_series():
		return(pd.read_csv(settings.File_Locations.bls_employment_location, converters={"state_code":utilities.check_state_code})) # read in states with leading zeroes, per FIPS

	def bls_laborforce_series():
		return(pd.read_csv(settings.File_Locations.bls_laborforce_location, converters={"state_code":utilities.check_state_code})) # read in states with leading zeroes, per FIPS

	def bls_wage_series():
		return(pd.read_csv(settings.File_Locations.bls_wage_location, converters={"state_code":utilities.check_state_code})) # read in states with leading zeroes, per FIPS