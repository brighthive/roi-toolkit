import numpy as np
import pandas as pd
import warnings
from pandas.api.types import is_numeric_dtype
from roi import settings

class Data:
	state_crosswalk = {
		"AL":"01",
		"AK":"02",
		"AZ":"04",
		"AR":"05",
		"CA":"06",
		"CO":"08",
		"CT":"09",
		"DE":"10",
		"DC":"11",
		"FL":"12",
		"GA":"13",
		"HI":"15",
		"ID":"16",
		"IL":"17",
		"IN":"18",
		"IA":"19",
		"KS":"20",
		"KY":"21",
		"LA":"22",
		"ME":"23",
		"MD":"24",
		"MA":"25",
		"MI":"26",
		"MN":"27",
		"MS":"28",
		"MO":"29",
		"MT":"30",
		"NE":"31",
		"NV":"32",
		"NH":"33",
		"NJ":"34",
		"NM":"35",
		"NY":"36",
		"NC":"37",
		"ND":"38",
		"OH":"39",
		"OK":"40",
		"OR":"41",
		"PA":"42",
		"PR":"72",
		"RI":"44",
		"SC":"45",
		"SD":"46",
		"TN":"47",
		"TX":"48",
		"UT":"49",
		"VT":"50",
		"VA":"51",
		"VI":"78",
		"WA":"53",
		"WV":"54"
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

def State_To_FIPS_series(state_abbreviation_series):
	crosswalk = Data.state_crosswalk
	mapped = check_state_code_series(state_abbreviation_series.map(crosswalk))
	return(mapped)

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

def age_to_group(pandas_series):
		cut_series = pd.cut(pandas_series, bins=[0,18,25,34,54,64,150], right=True, labels=['18 and under','19-25','26-34','35-54','55-64','65+']).astype(str)
		return(cut_series)

def multiple_describe(frame_, grouping_factors, value_column_name):
	grouped = frame_.groupby(grouping_factors, as_index=False)[value_column_name].agg({'n':np.size,'mean':np.mean, 'median':np.median, 'sd':np.std, 'min':np.min, 'max':np.max})
	return(grouped)

def dataframe_groups_to_ndarray(dataframe, groupby_columns, value_to_groups):
	"""
	This method takes a pandas dataframe and yields a numpy array of arrays containing values split up by group.

	Parameters:
	-----------
	dataframe : Pandas DataFrame
		Dataframe containing microdata with object or factor variables denoting groups

	groupby_columns : list(str)
		list of column names e.g. "gender" or "race"

	value_to_groups : str
		Column name containing the value which will be split into groups

	Returns
	-------
	A tuple: (numpy[N] with group names, multidimensional array with as many sub-arrays (N) as groups)
	"""
	grouped = dataframe.groupby(groupby_columns)[value_to_groups].apply(lambda x: np.array(x.values))
	groups = np.array(grouped.index)
	list_of_values = np.asarray(grouped)
	return (groups, list_of_values)

class Local_Data:
	def all_mean_wages():
		return(pd.read_csv(settings.File_Locations.mean_wages_location, converters={"state_code":check_state_code}))

	def hs_grads_mean_wages():
		return(pd.read_csv(settings.File_Locations.hs_mean_wages_location, converters={"STATEFIP":check_state_code}))

	def mincer_params():
		return(pd.read_pickle(settings.File_Locations.mincer_params_location))

	def cpi_adjustments():
		return(pd.read_csv(settings.File_Locations.cpi_adjustments_location))

	def bls_employment_series():
		return(pd.read_csv(settings.File_Locations.bls_employment_location, converters={"state_code":check_state_code})) # read in states with leading zeroes, per FIPS

	def bls_laborforce_series():
		return(pd.read_csv(settings.File_Locations.bls_laborforce_location, converters={"state_code":check_state_code})) # read in states with leading zeroes, per FIPS

	def bls_wage_series():
		return(pd.read_csv(settings.File_Locations.bls_wage_location, converters={"state_code":check_state_code})) # read in states with leading zeroes, per FIPS

class Supporting:
	"""
	Class for miscellaneous supporting calculation functions.
	"""
	def group_aggregation(dataframe, aggregation_category_list, variable_to_aggregate, aggregation_method):
		"""
		This method is just a shortener for a groupby aggregation.

		Parameters:
		-----------
		dataframe : Pandas DataFrame
			Dataframe containing microdata

		aggregation_category_list : list(str)
			list of column names e.g. "gender" or "race"

		variable_to_aggregate : str
			Column name containing the value which will be aggregated

		aggregation_method: str
			Function name e.g. "mean" or "sum." Must be a legit function!

		Returns
		-------
		A dataframe with column for the aggregated value. If method is X and original value is Y, the aggregated column is X_Y.
		"""
		aggregated_name = "{}_{}".format(aggregation_method, variable_to_aggregate)
		aggregated = test_microdata.groupby(aggregation_category_list)[variable_to_aggregate].aggregate(aggregation_method).reset_index().rename(columns={variable_to_aggregate:aggregated_name})		
		return aggregated
