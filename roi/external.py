import requests
import json
import pandas as pd # using pandas here for the sake of (1) familiarity and (2) ease of extensibility
import numpy as np
import os
from datetime import date
from roi import settings, utilities
import warnings

"""
This submodule contains methods for communicating with external APIs and gathering data, mostly macroeconomic statistics,
than may be necessary for calculating robust ROI metrics in a U.S. setting.


##### BLS Resources #####

# Main Background:
https://www.bls.gov/cps/data.htm
# Of particular interest is the LE Series
https://download.bls.gov/pub/time.series/le/le.series

# Compressed flat files
https://download.bls.gov/pub/time.series/compressed/tape.format/

###### Figuring out LE series

There is no real documentation for this series - all the BLS offers is this site: https://download.bls.gov/pub/time.series/le/le.series
So we have to glean what we can from this page, which indicates that the format for these series is:

LE + seasonal adjustment code[1 - U/S] + ?[1] + lfst_code[2] + ?[5] ?[2]


"""

class Parameters:
	"""
	Paramaters for classes and methods in this submodule
	"""

	# These are codes used in the BLS API
	BLS_measure_codes = {
		"unemployment rate": "03",
		"unemployment": "04",
		"employment": "05",
		"labor force": "06"
	}

class BLS_API:
	"""
	This class contains methods needed for collecting data from the Bureau of Labor Statistics API.
	On init, it checks to see if if the environment variable BLS_API_KEY is set. If it's not set, it must
	be passed as the class instance's sole argument. If neither case obtains, the class will throw an error.

	The BLS API takes as a main argument Series IDs describing the type and format of data to be retrieved.
	The API takes start and and years as additional arguments, but geographic specifications, for example,
	need to be included as part of the series ID.

	Comments in this class don't explain all arguments related to BLS API calls. Each method contains a link to the API
	page for the associated series. Parameters subject to change in the other methods in this class are the only ones listed
	under parameters for each method.

	Parameters:
		bls_api_key : Key for the BLS API (optional)

	Attributes:
		self.bls_api_key : same as bls_api_key argument

	Reference:
		Series ID Formats: https://www.bls.gov/help/hlpforma.htm
		API FAQs: https://www.bls.gov/developers/api_faqs.htm

	"""
	def __init__(self, bls_api_key = None):
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
			Please see the BLS API documentation for comlete information about arguments to this method

		Returns:
			series_id : A string containing the a Series ID, to be passed to the BLS API. For most use cases, this method should be called with the default arguments.

		"""
		series_id = prefix + seasonal_adjustment_code + periodicity + area_code + base_code + item_code
		return series_id

	def employment_series_id(self, state_code, prefix="LA", seasonal_adjustment_code="U", measure_code="employment"):
		"""

		Form Series ID for Local Area Unemployment statistics (prefix LA) from the BLS.

		Parameters:
			measure_code : str, One of "unemployment rate", "unemployment", "employment", "labor force". See class Parameters.BLS_measure_codes, which provides a useful dict that translates these into the numerical codes used by the API.

		Returns:
			series_id : A string containing the a Series ID, to be passed to the BLS API.

		"""
		state_code = utilities.check_state_code(state_code)

		area_code = "ST{}00000000000".format(state_code)
		measure_code = Parameters.BLS_measure_codes[measure_code]
		series_id = prefix + seasonal_adjustment_code + area_code + measure_code
		return series_id

	def wage_series_id(self, state_code, prefix="SM", seasonal_adjustment_code="U", area_code="00000", industry_code="05000000", data_type_code="11"):
		"""

		Form Series ID for weekly wage statistics (prefix SM) from the BLS. 

		Parameters:
			state_code : str, State-level FIPS codes as strings, e.g. "08" for Colorado.

		Returns:
			series_id : A string containing the a Series ID, to be passed to the BLS API.

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
			series_id    :    str, Series ID formed by wage_series_id(), employment_series_id(), etc.
			startyear    :    int or str, Year when we want the data to start
			endyear      :    int or str, Year when we want the data to end


		Returns:
			content      :     string containing BLS API response as JSON

		"""
		api_key = self.bls_api_key
		url = ("https://api.bls.gov/publicAPI/v2/timeseries/data/{}?startyear={}&endyear={}&registrationkey={}".format(seriesid, str(startyear), str(endyear), api_key))
		response = requests.get(url)
		content = response.content
		return content

	def parse_api_response(self, json_response):
		"""

		Take the response from the BLS API, passed as a string, parse the JSON, remove excess data, and convert dates to datetimes.

		Parameters:
			json_response :    str, response from BLS API

		Returns:
			data_frame    :    dataframe containing parsed response.

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

		Parameters:
			start_year   :  str or int, start year
			end_year     :  str or int, end year

		Returns:
			adjustment   :  Float representing adjustment factor

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
		This is identical to get_cpi_adjustment() except it returns the CPI indices for the given range, so it returns a dataframe
		Remember - it takes a maximum of twenty years!

		Because the CPI-U returns an index using 1982 as a base year, we average the index within each year to get a year-level inflation index.
		This smooths volatility in CPI. This function can be modified to return monthly figures, but the default is to return
		the annual mean in order to discourage analyses based on statistical artifacts. For example, students who happen
		to enter a program in a CPI trough and exit in a CPI peak will appear to have gained more in terms of earnings
		than we might reasonably conclude they actually had.

		This function also sets the CPI adjustment series as an attribute of the parent class BLS_API().

		Parameters:
			start_year : str or int, start year
			end_year : str or int, end year

		Returns:
			annual : Dataframe representing national CPI indices at the national level for January in each year in the range provided.
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
		"""
		This is the main method for fetching historical employment data for a given state and set of years.

		Parameters:
			state_code :  State FIPS code, e.g. "08" 
			start_year :  Start year
			end_year   :  End year
			measure    :  Measure. Must be one of ["employment", "labor force"]

		Returns:
			employment : A dataframe containing the relevant employment statistic specified by measure.

		"""
		series_id = self.employment_series_id(state_code=state_code, measure_code=measure)
		raw_response = self.get_series(series_id, start_year, end_year)
		employment = self.parse_api_response(raw_response)
		
		if measure == "labor force":
			self.bls_laborforce_series = employment
		elif measure == "employment":
			self.bls_employment_series = employment

		return(employment)

	def get_wage_data(self, state_code, start_year, end_year):
		"""
		This is the main method for fetching historical employment data for a given state and set of years.

		Parameters:
			state_code :  State FIPS code, e.g. "08" 
			start_year :  Start year
			end_year   :  End year

		Returns:
			employment : A dataframe containing historical wage data for the specified state and time period

		"""
		series_id = self.wage_series_id(state_code=state_code)
		raw_response = self.get_series(series_id, start_year, end_year)
		wage = self.parse_api_response(raw_response)
		self.bls_wage_series = wage
		return(wage)

	def make_employment_rate_frame(self, employment_series, laborforce_series):
		"""
		Creates a dataframe containing the employment rate for a set of states and month/year periods.
		The employment and labor force methods return absolute figures, so rates must be calcualte

		Parameters:
			employment_series   :   A dataframe structurally identical to that produced by get_employment_data(..., measure="employment")
			laborforce_series   :   A dataframe structurally identical to that produced by get_employment_data(..., measure="labor force")

		Returns:
			final               :   A dataframe containing employment rate (for labor force participants) in the given locations over the given time period

		"""
		employment_rate_series = employment_series.merge(laborforce_series, on=["state_code", "month_year"], suffixes=("_emp","_labor"))
		employment_rate_series['employment_rate'] = employment_rate_series['value_emp'] / employment_rate_series['value_labor']
		final = employment_rate_series[['state_code','month_year','employment_rate']]
		return(final)


class Census:
	"""
	As of this writing, (12/09/2020), the main purpose of this class is to fetch geocodes from the Census Geocoder API.
	For more detail, please see https://geocoding.geo.census.gov/geocoder/Geocoding_Services_API.pdf
	"""

	def get_batch_geocode(dataframe):
		"""
		Fetches a 12-digit FIPS code from the Census Geocoder API for a dataframe passed as this function's sole argument.

		Unlike other methods in the ROI Toolkit, this method must take a dataframe that has columns with specific column names and contents.

		These columns are:
			id             :        A unique identifier for each address
			Address        :        A street address, e.g. "42 Zaphod Beeblebrox Avenue"
			City           :        A city, e.g. "New York" or "New York City"
			State          :        A two-digit state postal code such as "CA"
			Zip            :        A ZIP5 code, such as "90210"

		The Geocoder returns a JSON object containing all relevant geographic data, such as latitude and longitude.
		But this function simply takes the components necessary to create a GEOID at the block group level.
		Block groups very roughly correspond to neighborhoods.

		We use the JSON response here to form GEOID as follows with COMPONENTS[LENGTH]: STATE[2] + COUNTY[3] + TRACT[6] + BLOCK GROUP[1] = GEOID[12]

		Parameters:
			dataframe     :       A dataframe with the columns outlined above

		Returns:
			geocodes:      :      A pandas dataframe ordered in the same order as dataframe containing twelve-digit codes -- as a string -- denoting a neighborhood-sized region in the United States.
		"""

		dataframe.to_csv("temp_addresses_frame.csv", index=False, header=None)
		files = {'addressFile': open('temp_addresses_frame.csv', 'rb')}

		url = "https://geocoding.geo.census.gov/geocoder/geographies/addressbatch?benchmark=9&vintage=Census2010_Census2010"

		# first fetch response
		try:
			response = requests.post(url, files=files)
			response_content = response.content
		except Exception as e:
			print("EXCEPTION: Couldn't get geocoding API response for FILE")

		# turn response into dataframe
		try:
			bytes_to_csv = StringIO(str(response_content,'utf-8'))
			df = pd.read_csv(bytes_to_csv, names=['id','provided_address','match','matchtype','clean_address','latlon','tiger_line_id','side_of_street','statefip','county','tract','block'], dtype=str).fillna("")
		except Exception as e:
			print("EXCEPTION: Failed parsing Census batch geocoder response into CSV: {}".format(e))

		# combine variables to get a geocode
		df['block_group'] = df['block'].astype(str).str.slice(start = 0, stop = 1)
		df['geocode'] = df['statefip'] + df['county'] + df['tract'] + df['block_group']

		# make id string for merging
		df['id'] = df['id'].astype(int)

		# where did we have blank responses?
		null_geocode = (df['geocode'] != "")
		successful_responses = df[null_geocode]

		# merge with original - dump non-geocode variables for now!
		response_to_merge = successful_responses[['id','geocode']]
		to_return = dataframe.merge(response_to_merge, how='left', on='id', left_index=True).set_index(dataframe.index).fillna("") # set index is important!

		succesfully_merged = round(100*null_geocode.mean(),2)
		exact_matches = round(100*(successful_responses['matchtype'] == "Exact").mean(),2)

		print("Successfully geocoded {}% of {} passed addresses.".format(succesfully_merged, len(df)))
		print("Of successfully matched addresses, {}% were exact matches".format(exact_matches))

		geocodes = to_return['geocode']

		return(geocodes)

	def get_geocode_for_address(address, city, state_code):
		"""
		Fetches a 12-digit FIPS code from the Census Geocoder API.

		The Geocoder returns a JSON object containing all relevant geographic data, such as latitude and longitude.
		But this function simply takes the components necessary to create a GEOID at the block group level.
		Block groups roughly correspond to neighborhoods.

		We use the JSON response here to form GEOID as follows with COMPONENTS[LENGTH]: STATE[2] + COUNTY[3] + TRACT[6] + BLOCK GROUP[1] = GEOID[12]

		Parameters:
			address    : str, street address e.g. "42 Zaphod Beeblebrox Avenue"
			city       : str, city name e.g. "Prefectville"
			state_code : str, two-digit state postal code e.g.: "CA" or "NY"

		Returns:
			geocode    : A twelve-digit code -- as a string -- denoting a neighborhood-sized region in the United States.
		"""

		url = "https://geocoding.geo.census.gov/geocoder/geographies/address?street={}&city={}&state={}&benchmark=9&format=json&vintage=Census2010_Census2010".format(address, city, state_code)

		# first fetch response
		try:
			response = requests.get(url)
			response_content = response.content
			response_parsed = json.loads(response_content)
		except Exception as e:
			print("EXCEPTION: Couldn't get geocoding API response for {}:\n 	{}".format(address, e))

		# access necessary elements
		try:
			first_address_match = response_parsed['result']['addressMatches'][0]
			first_address_match_geographies = first_address_match['geographies']
			tract_geoid = str(first_address_match_geographies['Census Tracts'][0]['GEOID'])
			block_group = str(first_address_match_geographies['Census Blocks'][0]['BLKGRP'])
			geocode = "{}{}".format(tract_geoid, block_group)
			return(geocode)
		except Exception as e:
			#print(response_parsed)
			print("EXCEPTION: Couldn't access vital response elements in geocode API response:\n 	{}".format(e))
			return ""


def fetch_bls_data(start_year, end_year, bls_api_key=None):
	"""
	This is a very important function! When run, fetch_bls_data() will fetch employment, labor force, wage and inflation
	time series from the BLS for all years in the range start_year:end_year and for all states in the U.S.

	Once this is done, it will save them to disk as CSVs (for human-readability). Having these datasets saved on disk
	is necessary for using any of the methods in the macro submodule. There are two groups of people who should execute this function:

	(1) Maintainers of the roi-toolkit repo, who should run it in order to keep the repo updated with the latest data, which is packaged with the module
	(2) Any user of the repo who wants to replace the data that is packaged with it with more up-to-date statistics.

	File locations are located in settings.py

	Parameters:
		start_year   :   Start year YYYY
		end_year     :   End year   YYYY

	Returns:
		None
	"""
	bls = BLS_API(bls_api_key)
	
	# set up data frames
	employment_dataframe = pd.DataFrame()
	wage_dataframe = pd.DataFrame()
	labor_force_dataframe = pd.DataFrame()

	# loop over FIPS codes to get wage and unemployment data for every state
	for state_code in utilities.Data.state_crosswalk.values():

		# absolute employment numbers
		emp_series_id = bls.employment_series_id(state_code=state_code)
		emp_raw_response = bls.get_series(emp_series_id, start_year, end_year)

		# absolute labor force numbers
		lf_series_id = bls.employment_series_id(state_code=state_code, measure_code="labor force")
		lf_raw_response = bls.get_series(lf_series_id, start_year, end_year)

		# absolute wage numbers - UNADJUSTED
		wage_series_id = bls.wage_series_id(state_code=state_code)
		wage_raw_response = bls.get_series(wage_series_id, start_year, end_year)

		try:
			employment = bls.parse_api_response(emp_raw_response)
			laborforce = bls.parse_api_response(lf_raw_response)
			wage = bls.parse_api_response(wage_raw_response)
		except Exception as E:
			# Errors are caught here and the loop continues. Read the output!
			print("Failed fetching data for {}".format(state_code))
			print(E)
			continue

		# Set state code columns for each datagrame
		employment['state_code'] = state_code
		laborforce['state_code'] = state_code
		wage['state_code'] = state_code

		# append dataframes
		employment_dataframe = employment_dataframe.append(employment)
		wage_dataframe = wage_dataframe.append(wage)
		labor_force_dataframe = labor_force_dataframe.append(laborforce)
		print("Fetched BLS data for {}!".format(state_code))

	# create employment rate series
	employment_rate_dataframe = bls.make_employment_rate_frame(employment_dataframe, labor_force_dataframe)

	# save CSVs
	employment_dataframe.to_csv(settings.File_Locations.bls_employment_location, index=False)
	labor_force_dataframe.to_csv(settings.File_Locations.bls_laborforce_location, index=False)
	wage_dataframe.to_csv(settings.File_Locations.bls_wage_location, index=False)
	employment_rate_dataframe.to_csv(settings.File_Locations.bls_employment_rate_location, index=False)

	# get cpi data
	cpi = bls.get_cpi_adjustment_range(1999, end_year) # start in 1999 always - this is the base year for CPS adjusted income
	cpi.to_csv(settings.File_Locations.cpi_adjustments_location, index=False)

	return(None)