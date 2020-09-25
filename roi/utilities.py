import numpy as np
import pandas as pd

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
	# hardcoded - FIPS aren't changing anytime soon
	crosswalk = {
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

	if state_abbreviation not in crosswalk.keys():
		raise ValueError("{} is not a valid state abbreviation. State_To_FIPS() requires an abbreviation like CA.".format(state_abbreviation))
	else:
		return(crosswalk[state_abbreviation])

	return(None)