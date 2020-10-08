import requests
import json
import pandas as pd # using pandas here for the sake of (1) familiarity and (2) ease of extensibility
import numpy as np
import os
from datetime import date
from roi import settings, get_data, utilities
import warnings

"""

##### Notes #####

# Main Background:
https://www.bls.gov/cps/data.htm
# Of particular interest is the LE Series
https://download.bls.gov/pub/time.series/le/le.series

# Compressed flat files
https://download.bls.gov/pub/time.series/compressed/tape.format/

###### Important things to know

Important things to know from https://www.bls.gov/developers/api_faqs.htm

How many requests can I make daily?
Registered users may request up to 500 queries daily. Unregistered users may request up to 25 queries daily.
 
How many series can I include in a query?
Registered users may request up to 50 series per query. Unregistered users may request up to 25 series per query.

###### Figuring out LE series

There is no real documentation for this series - all the BLS offers is this site: https://download.bls.gov/pub/time.series/le/le.series
So we have to glean what we can from this page, which indicates that the format for these series is:

LE + seasonal adjustment code[1 - U/S] + ?[1] + lfst_code[2] + ?[5] ?[2]


"""

example_response = '{"status":"REQUEST_SUCCEEDED","responseTime":137,"message":[],"Results":{\n"series":\n[{"seriesID":"LAUST080000000000006","data":[{"year":"2019","period":"M10","periodName":"October","latest":"true","value":"3178070","footnotes":[{"code":"P","text":"Preliminary."}]},{"year":"2019","period":"M09","periodName":"September","value":"3177825","footnotes":[{}]},{"year":"2019","period":"M08","periodName":"August","value":"3173865","footnotes":[{}]},{"year":"2019","period":"M07","periodName":"July","value":"3189419","footnotes":[{}]},{"year":"2019","period":"M06","periodName":"June","value":"3186284","footnotes":[{}]},{"year":"2019","period":"M05","periodName":"May","value":"3127934","footnotes":[{}]},{"year":"2019","period":"M04","periodName":"April","value":"3119039","footnotes":[{}]},{"year":"2019","period":"M03","periodName":"March","value":"3123249","footnotes":[{}]},{"year":"2019","period":"M02","periodName":"February","value":"3132592","footnotes":[{}]},{"year":"2019","period":"M01","periodName":"January","value":"3118999","footnotes":[{}]},{"year":"2018","period":"M13","periodName":"Annual","value":"3096358","footnotes":[{}]},{"year":"2018","period":"M12","periodName":"December","value":"3136729","footnotes":[{}]},{"year":"2018","period":"M11","periodName":"November","value":"3133401","footnotes":[{}]},{"year":"2018","period":"M10","periodName":"October","value":"3135286","footnotes":[{}]},{"year":"2018","period":"M09","periodName":"September","value":"3124018","footnotes":[{}]},{"year":"2018","period":"M08","periodName":"August","value":"3114611","footnotes":[{}]},{"year":"2018","period":"M07","periodName":"July","value":"3126894","footnotes":[{}]},{"year":"2018","period":"M06","periodName":"June","value":"3115771","footnotes":[{}]},{"year":"2018","period":"M05","periodName":"May","value":"3071539","footnotes":[{}]},{"year":"2018","period":"M04","periodName":"April","value":"3060983","footnotes":[{}]},{"year":"2018","period":"M03","periodName":"March","value":"3056824","footnotes":[{}]},{"year":"2018","period":"M02","periodName":"February","value":"3054983","footnotes":[{}]},{"year":"2018","period":"M01","periodName":"January","value":"3025258","footnotes":[{}]},{"year":"2017","period":"M13","periodName":"Annual","value":"2992412","footnotes":[{}]},{"year":"2017","period":"M12","periodName":"December","value":"3022280","footnotes":[{}]},{"year":"2017","period":"M11","periodName":"November","value":"3027893","footnotes":[{}]},{"year":"2017","period":"M10","periodName":"October","value":"3030716","footnotes":[{}]},{"year":"2017","period":"M09","periodName":"September","value":"3035085","footnotes":[{}]},{"year":"2017","period":"M08","periodName":"August","value":"3019660","footnotes":[{}]},{"year":"2017","period":"M07","periodName":"July","value":"3019734","footnotes":[{}]},{"year":"2017","period":"M06","periodName":"June","value":"3007314","footnotes":[{}]},{"year":"2017","period":"M05","periodName":"May","value":"2966441","footnotes":[{}]},{"year":"2017","period":"M04","periodName":"April","value":"2957983","footnotes":[{}]},{"year":"2017","period":"M03","periodName":"March","value":"2952018","footnotes":[{}]},{"year":"2017","period":"M02","periodName":"February","value":"2945602","footnotes":[{}]},{"year":"2017","period":"M01","periodName":"January","value":"2924216","footnotes":[{}]}]}]\n}}'

class Parameters:
	BLS_measure_codes = {
		"unemployment rate": "03",
		"unemployment": "04",
		"employment": "05",
		"labor force": "06"
	}

class BLS_API:
	"""
	Functions needed for collecting data from the Bureau of Labor Statistics API and conducting some operations on it.

	The BLS API takes as a main argument Series IDs describing the type and format of data to be retrieved.
	The API takes start and and years as additional arguments, but geographic specifications, for example,
	need to be included as prat of the series ID.

	Comments in this class don't explain all arguments related to BLS API calls. Each method contains a link to the API
	page for the associated series. Parameters subject to change in the other methods in this class are the only ones listed
	under parameters for each method.

	Reference:
	---------
	Series ID Formats:
		https://www.bls.gov/help/hlpforma.htm

	API FAQs:
		https://www.bls.gov/developers/api_faqs.htm

	"""
	def __init__(self, bls_api_key = None, query=True):

		if query == False:
			print("When query=False, ROI Toolkit BLS_API will attempt to locate a local tabular file containing the results of a previous query. By default, this data is located in roi/data/bls.")
			self.bls_wage_series = get_data.bls_wage_series()
			self.bls_employment_series = get_data.bls_employment_series()
			self.bls_laborforce_series = get_data.bls_laborforce_series()
			self.cpi_adjustment_series = get_data.cpi_adjustments()
			self.employment_rate_series = self.make_employment_rate_frame(self.bls_employment_series, self.bls_laborforce_series)
		else: 
			if (bls_api_key is None):
				bls_api_key = os.getenv('BLS_API_KEY') # unnecessary for BLS series 1.0 api but series 2 API overcomes #extreme rate limiting
				if bls_api_key is None:
					raise NameError("The BLS_API class requires that you provide an API key to the Bureau of Labor Statistics API. You can pass this key directly when instantiating the class (e.g. BLS_API(YOUR_KEY_HERE) or (preferably) by setting an environment variable called BLS_API_KEY. For more information please see the BLS API docs at: https://www.bls.gov/developers/api_faqs.htm")
				else:
					self.bls_api_key = bls_api_key
			else:
				self.bls_api_key = bls_api_key

	def get_cpi(self, prefix="CU", seasonal_adjustment_code="S", periodicity="R", area_code="0000", base_code="S", item_code="A0"):
		"""

		Form sequence ID for the CPI-U: The Consumer Price Index for Urban Consumers.
		This is an index of inflation that is (as of 12/2019) returned with base year 1982, where the CPI-U = 100.

		Parameters:
		-----------
		area_code : str
			"0000" is the nationwide code. Realistically, this is what should be used.

		Returns:
		-------
		A string containing the a Series ID, to be passed to the BLS API.

		"""
		series_id = prefix + seasonal_adjustment_code + periodicity + area_code + base_code + item_code
		return series_id

	def employment_series_id(self, state_code, prefix="LA", seasonal_adjustment_code="U", measure_code="employment"):
		"""

		Form Series ID for Local Area Unemplyoment statistics (prefix LA) from the BLS.

		Parameters:
		-----------
		measure_code : str
			One of "unemployment rate", "unemployment", "employment", "labor force".
			See class Parameters.BLS_measure_codes, which provides a useful dict that translates these into the numerical codes used by the API.

		Returns:
		-------
		A string containing the a Series ID, to be passed to the BLS API.

		"""
		state_code = utilities.check_state_code(state_code)

		area_code = "ST{}00000000000".format(state_code)
		measure_code = Parameters.BLS_measure_codes[measure_code]
		series_id = prefix + seasonal_adjustment_code + area_code + measure_code
		return series_id

	def wage_series_id(self, state_code, prefix="SM", seasonal_adjustment_code="U", area_code="00000", industry_code="05000000", data_type_code="11"):
		"""

		Form Series ID for ____________ statistics (prefix SM) from the BLS. 

		Parameters:
		-----------
		state_code : str
			State-level FIPS codes as strings, e.g. "08" for Colorado.

		Returns:
		-------
		A string containing the a Series ID, to be passed to the BLS API.

		"""
		state_code = utilities.check_state_code(state_code)

		# data type 11 = average weekly earnings
		series_id = prefix + seasonal_adjustment_code + state_code + area_code + industry_code + data_type_code
		return series_id

	def get_series(self, seriesid, startyear, endyear):
		"""

		Fetch API response from BLS API.
		Please note that the API returns a *MAXIMUM* of 20 years of data.
		Data is returned as JSON at the year/month level.

		Parameters:
		-----------
		series_id : str
			Series ID formed by wage_series_id(), employment_series_id(), etc.

		startyear: int or str
			Year when we want the data to start

		endyear: int or str
			Year when we want the data to end


		Returns:
		-------
		string containing API response as JSON

		"""
		api_key = self.bls_api_key
		url = ("https://api.bls.gov/publicAPI/v2/timeseries/data/{}?startyear={}&endyear={}&registrationkey={}".format(seriesid, str(startyear), str(endyear), api_key))
		response = requests.get(url)
		content = response.content
		return content

	def parse_api_response(self, json_response):
		"""

		Take the response from the BLS API, passed as a string, parse the JSON, remove excess columns, and convert dates to datetimes.

		Parameters:
		-----------
		json_response : str
			Response from BLS API

		Returns:
		-------
		dataframe containing parsed response.

		"""
		parsed = json.loads(json_response)
		data_only = parsed['Results']['series'][0]['data']
		data_frame = pd.DataFrame(data_only)

		# remove unnecessary columns
		data_frame = data_frame.drop(['footnotes', 'latest', 'period'], axis=1, errors='ignore')

		# make sure value is float
		try:
			data_frame['value'] = data_frame['value'].astype(float)
		except:
			raise Exception("parse_api_response() couldn't find 'value' in BLS API response. Printing raw response: {}".format(json_response))

		# errors are coerced so that "Annual" dates go to NaN
		data_frame['month_year'] = pd.to_datetime(data_frame.periodName + " " + data_frame.year, format='%B %Y', errors='coerce').dt.strftime('%Y-%m')

		return(data_frame)

	def get_cpi_adjustment(self, start_year, end_year):
		"""
		For any pair of years, return the CPI adjustment factor for that pair of years. E.g. if the adjustment factor between
		2000 and 2020 is 1.5, then $100 in 2000 is roughly equal in value to $150 in 2020. 

		The CPI API returns only twenty years of data, and the time frame we are interested in may (will) span longer than twenty years.
		So to avoid that (pretty unlikely situation), for any pair of years, we make two requests and simply return the adjustment factor

		IMPORTANT:
		Month/year data is a little bit too granular for our purposes so this function returns the CPI index for January of each year.

		Parameters:
		-----------
		start_year : str or int
			start year

		end_year : str or int
			end year

		Returns:
		-------
		Float representing adjustment factor

		"""
		series_id = self.get_cpi()
		series_start = self.get_series(series_id, start_year, start_year)
		series_end = self.get_series(series_id, end_year, end_year)

		try:
			start_frame = self.parse_api_response(series_start)
			end_frame = self.parse_api_response(series_end)
			start_cpi = start_frame['value'].mean()#.loc[start_frame.periodName == "January", "value"].iat[0]
			end_cpi = end_frame['value'].mean()#.loc[end_frame.periodName == "January", "value"].iat[0]
		except Exception as e:
			raise Exception("Error fetching BLS CPI Statistics: {}".format(e))

		adjustment = end_cpi/start_cpi
		return(adjustment)

	def get_cpi_adjustment_range(self, start_year, end_year):
		"""
		Thehis is identical to get_cpi_adjustment() except it returns the CPI indices for the given range, so it returns a dataframe
		Remember - it takes a maximum of twenty years!

		Because the CPI-U returns an index using 1982 as a base year, we average the index to get a year-level inflation index.

		Parameters:
		-----------
		start_year : str or int
			start year

		end_year : str or int
			end year

		Returns:
		-------
		Dataframe representing national CPI indices at the national level for January in each year in the range provided.
		"""
		if (int(end_year) - int(start_year) > 20):
			raise Exception("get_cpi_adjustment_range({}, {}) offered more than 20 years of data; API returns only 20 years".format(str(start_year), str(end_year)))

		series_id = self.get_cpi()
		series = self.get_series(series_id, start_year, end_year)
		series_frame = self.parse_api_response(series)

		#convert monthly to annual figures
		annual = series_frame.groupby('year')['value'].mean().reset_index().rename(columns={"value":"cpi"})
		self.cpi_adjustment_series = annual
		return(annual)

	def get_employment_data(self, state_code, start_year, end_year, measure):

		# measure must be one of ["employment", "labor force"]
		series_id = self.employment_series_id(state_code=state_code, measure_code=measure)
		raw_response = self.get_series(series_id, start_year, end_year)
		employment = self.parse_api_response(raw_response)
		
		if measure == "labor force":
			self.bls_laborforce_series = employment
		elif measure == "employment":
			self.bls_employment_series = employment

		return(employment)


	def get_wage_data(self, state_code, start_year, end_year):

		series_id = self.wage_series_id(state_code=state_code)
		raw_response = self.get_series(series_id, start_year, end_year)
		wage = self.parse_api_response(raw_response)
		self.bls_wage_series = wage
		return(wage)

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

	def make_employment_rate_frame(self, employment_series, laborforce_series):
		employment_rate_series = employment_series.merge(laborforce_series, on=["state_code", "month_year"], suffixes=("_emp","_labor"))
		employment_rate_series['employment_rate'] = employment_rate_series['value_emp'] / employment_rate_series['value_labor']
		final = employment_rate_series[['state_code','month_year','employment_rate']]
		return(final)

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


if __name__ == "__main__":
	#### examples

	cpi_data = BLS_API.get_cpi_adjustment_range(2000,2019)
	print(cpi_data)
	exit()


	# series ids
	employment_series_id = BLS_API.employment_series_id(measure_code="employment")
	labor_force_series_id = BLS_API.employment_series_id(measure_code="labor force")
	wage_series_id = BLS_API.wage_series_id()

	# series retreived
	employment_raw = BLS_API.get_series(employment_series_id, 2014, 2018)
	labor_force_raw = BLS_API.get_series(labor_force_series_id, 2014, 2018)
	wage_raw = BLS_API.get_series(wage_series_id, 2014, 2018)

	print(employment_raw)
	exit()

	# to dataframes
	employment = BLS_API.parse_api_response(employment_raw)
	labor_force = BLS_API.parse_api_response(labor_force_raw)
	wage = BLS_API.parse_api_response(wage_raw)
	
	employment.to_pickle('employment_pickled.pkl')
	labor_force.to_pickle('labor_force_pickled.pkl')
	wage.to_pickle('wage_pickled.pkl')
	
	employment = pd.read_pickle('employment_pickled.pkl')
	labor_force = pd.read_pickle('labor_force_pickled.pkl')
	wage = pd.read_pickle('wage_pickled.pkl')

	employment_change_example = Calculations.employment_change(employment, labor_force, "2015-09", "2018-05")
	wage_change_example = Calculations.wage_change(wage, "2015-09", "2018-05")

	print(wage_change_example)
	

