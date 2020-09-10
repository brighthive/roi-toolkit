import requests
import json
import pandas as pd # using pandas here for the sake of (1) familiarity and (2) ease of extensibility
import numpy as np
import os
from datetime import date
from roi import settings

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

BLS_API_KEY = os.getenv('BLS_API_KEY') # unnecessary for BLS series 1.0 api but series 2 API overcomes #extreme rate limiting

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
	page for the associated series. Parameters subject to change in the other methods in this class are the only opnes listed
	under parameters for each method.

	Reference:
	---------
	Series ID Formats:
		https://www.bls.gov/help/hlpforma.htm

	API FAQs:
		https://www.bls.gov/developers/api_faqs.htm

	"""
	def get_cpi(prefix="CU", seasonal_adjustment_code="S", periodicity="R", area_code="0000", base_code="S", item_code="A0"):
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

	def employment_series_id(prefix="LA", seasonal_adjustment_code="U", state_code="08", measure_code="employment"):
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
		area_code = "ST{}00000000000".format(state_code)
		measure_code = Parameters.BLS_measure_codes[measure_code]
		series_id = prefix + seasonal_adjustment_code + area_code + measure_code
		return series_id

	def wage_series_id(prefix="SM", seasonal_adjustment_code="U", state_code="08", area_code="00000", industry_code="05000000", data_type_code="11"):
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
		# data type 11 = average weekly earnings
		series_id = prefix + seasonal_adjustment_code + state_code + area_code + industry_code + data_type_code
		return series_id

	def get_series(seriesid, startyear, endyear, api_key=BLS_API_KEY):
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

		url = ("https://api.bls.gov/publicAPI/v2/timeseries/data/{}?startyear={}&endyear={}&registrationkey={}".format(seriesid, str(startyear), str(endyear), api_key))
		response = requests.get(url)
		content = response.content
		return content

	def parse_api_response(json_response):
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
		data_frame['value'] = data_frame['value'].astype(float)

		# errors are coerced so that "Annual" dates go to NaN
		data_frame['month_year'] = pd.to_datetime(data_frame.periodName + " " + data_frame.year, format='%B %Y', errors='coerce').astype('datetime64[M]')

		return(data_frame)

	def get_cpi_adjustment(start_year, end_year):
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
		series_id = BLS_API.get_cpi()
		series_start = BLS_API.get_series(series_id, start_year, start_year)
		series_end = BLS_API.get_series(series_id, end_year, end_year)

		try:
			start_frame = BLS_API.parse_api_response(series_start)
			end_frame = BLS_API.parse_api_response(series_end)
			start_cpi = start_frame.loc[start_frame.periodName == "January", "value"].iat[0]
			end_cpi = end_frame.loc[end_frame.periodName == "January", "value"].iat[0]
		except Exception as e:
			print ("Error fetching BLS CPI Statistics: {}".format(e))
			exit()

		adjustment = end_cpi/start_cpi
		return(adjustment)

	def get_cpi_adjustment_range(start_year, end_year):
		"""
		This is identical to get_cpi_adjustment() except it returns the CPI indices for the given range, so it returns a dataframe
		Remember - it takes a maximum of twenty years!

		Again - returning January measurements only.

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

		series_id = BLS_API.get_cpi()
		series = BLS_API.get_series(series_id, start_year, end_year)
		series_frame = BLS_API.parse_api_response(series)
		series_frame_reduced = series_frame[series_frame.periodName == "January"].rename(columns={"value":"cpi"})[['year','cpi']]

		return(series_frame_reduced)

	def cpi_adjust_frame(frame_, wage_column, wage_year_column, year=date.today().year):
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
		adjustment_frame = BLS_API.get_cpi_adjustment_range(year - 20, year)
		current_year_cpi = adjustment_frame.loc[adjustment_frame.year == year, 'cpi'].iat[0]
		adjusted_frame = frame_.merge(adjustment_frame, left_on=wage_year_column, right_on='year', how='left')
		adjusted_frame['adjustment_factor'] = current_year_cpi/cpi
		adjusted_frame['adjusted_wage'] = adjusted_frame['adjustment_factor'] * adjusted_frame[wage_column]
		return adjusted_frame

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

	def employment_change(bls_employment_table, bls_labor_force_table, start_month, end_month):
		"""
		METHODOLOGICAL NOTE: This currently returns change in employment without reference to labor force status change.

		This function will probably have to be refactored as we move forward - this is basically just a skeleton.

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

		# configure dtype of input
		start_month_year = pd.to_datetime(start_month)
		end_month_year = pd.to_datetime(end_month)

		# get employment figures
		start_employment = bls_employment_table.loc[bls_employment_table.month_year == start_month, 'value'].astype(int).iat[0]
		end_employment = bls_employment_table.loc[bls_employment_table.month_year == end_month, 'value'].astype(int).iat[0]

		# get labor force figures
		start_labor_force = bls_labor_force_table.loc[bls_labor_force_table.month_year == start_month, 'value'].astype(int).iat[0]
		end_labor_force = bls_labor_force_table.loc[bls_labor_force_table.month_year == end_month, 'value'].astype(int).iat[0]

		# calculation
		employment_change = float((end_employment / end_labor_force) - (start_employment / start_labor_force))

		return employment_change

	def wage_change(bls_wage_table, start_month, end_month):
		"""
		METHODOLOGICAL NOTE: This currently returns change in employment without reference to labor force status change.

		This function will probably have to be refactored as we move forward - this is basically just a skeleton.

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

		bls_wage_table['bls_annual_wages'] = bls_wage_table['value'] * 52 # weekly wage to annual

		# configure dtype of input
		start_month_year = pd.to_datetime(start_month)
		end_month_year = pd.to_datetime(end_month)

		# get wage figures
		start_wage = bls_wage_table.loc[bls_wage_table.month_year == start_month, 'bls_annual_wages'].astype(int).iat[0]
		end_wage = bls_wage_table.loc[bls_wage_table.month_year == end_month, 'bls_annual_wages'].astype(int).iat[0]

		# calculation
		wage_change = end_wage - start_wage

		return wage_change



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
	

