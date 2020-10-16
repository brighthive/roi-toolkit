import requests
import json
import pandas as pd # using pandas here for the sake of (1) familiarity and (2) ease of extensibility
import numpy as np
import os
from datetime import date
from roi import settings, utilities
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

class Parameters:
	BLS_measure_codes = {
		"unemployment rate": "03",
		"unemployment": "04",
		"employment": "05",
		"labor force": "06"
	}

class BLS_API:
	"""
	Functions needed for collecting data from the Bureau of Labor Statistics API.

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
			self.bls_wage_series = utilities.Local_Data.bls_wage_series()
			self.bls_employment_series = utilities.Local_Data.bls_employment_series()
			self.bls_laborforce_series = utilities.Local_Data.bls_laborforce_series()
			self.cpi_adjustment_series = utilities.Local_Data.cpi_adjustments()
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

	def make_employment_rate_frame(self, employment_series, laborforce_series):
		employment_rate_series = employment_series.merge(laborforce_series, on=["state_code", "month_year"], suffixes=("_emp","_labor"))
		employment_rate_series['employment_rate'] = employment_rate_series['value_emp'] / employment_rate_series['value_labor']
		final = employment_rate_series[['state_code','month_year','employment_rate']]
		return(final)


class Census:

	def get_batch_geocode(dataframe):
		"""
		Fetches a 12-digit FIPS code from the Census Geocoder API.

		The Geocoder returns a JSON object containing all relevant geographic data, such as latitude and longitude.
		But this function simply takes the components necessary to create a GEOID at the block group level.
		Block groups roughly correspond to neighborhoods.

		We use the JSON response here to form GEOID as follows with COMPONENTS[LENGTH]: STATE[2] + COUNTY[3] + TRACT[6] + BLOCK GROUP[1] = GEOID[12]

		Parameters:
		-----------
		address : str
			Street address e.g. "42 Zaphod Beeblebrox Avenue"

		city : str
			City name e.g. "Prefectville"

		state_code : str
			Two-digit state postal code e.g.: "CA" or "NY"

		Returns
		-------
		A twelve-digit code -- as a string -- denoting a neighborhood-sized region in the United States.
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

		return(to_return['geocode'])

	def get_geocode_for_address(address, city, state_code):
		"""
		Fetches a 12-digit FIPS code from the Census Geocoder API.

		The Geocoder returns a JSON object containing all relevant geographic data, such as latitude and longitude.
		But this function simply takes the components necessary to create a GEOID at the block group level.
		Block groups roughly correspond to neighborhoods.

		We use the JSON response here to form GEOID as follows with COMPONENTS[LENGTH]: STATE[2] + COUNTY[3] + TRACT[6] + BLOCK GROUP[1] = GEOID[12]

		Parameters:
		-----------
		address : str
			Street address e.g. "42 Zaphod Beeblebrox Avenue"

		city : str
			City name e.g. "Prefectville"

		state_code : str
			Two-digit state postal code e.g.: "CA" or "NY"

		Returns
		-------
		A twelve-digit code -- as a string -- denoting a neighborhood-sized region in the United States.
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
			return "{}{}".format(tract_geoid, block_group)
		except Exception as e:
			#print(response_parsed)
			print("EXCEPTION: Couldn't access vital response elements in geocode API response:\n 	{}".format(e))
			return ""


class ADI (object):
	"""
	Methods related to the Area Deprivation Statistics
	Data can be downloaded from: https://www.neighborhoodatlas.medicine.wisc.edu/

	This object, at init, simply reads in the raw textfile of ADI indices at the block group level and forms it into quintiles.

	This currently uses the ADI based on the 2011-2015 ACS 5-year estimates.

	Block groups containing less than 100 persons, 30 housing units, or >33% of pop living in group quarters are suppressed
	with the value "PH". ADI indices are coerced to numeric, so suppressed indices are coerced to NaN.

	Finally, indices are bucketed into quintiles. IMPORTANT: Lower quintiles are HIGHER-SES. Higher quintiles are more deprived.
	"""
	def __init__(self):
		adi_location = settings.File_Locations.adi_location
		adi = pd.read_csv(adi_location, sep=',', dtype="str") # read in ADI by block group from text file
		adi['adi_natrank_numeric'] = pd.to_numeric(adi['adi_natrank'], errors='coerce')
		adi['adi_quintile'] = pd.qcut(adi['adi_natrank_numeric'], [0, 0.2, 0.4, 0.6, 0.8, 1], labels=["0-20","20-40","40-60","60-80","80-100"])
		self.adi_frame = adi
		return None

	def get_quintile_for_geocode(self, fips_geocode):
		"""
		Parameters:
		-----------
		fips_geocode : str
			Twelve-digit FIPS code

		adi_frame : Pandas DataFrame
			ADI Dataframe produced above in ADI.get_adi_frame()

		Returns
		-------
		A single string value such as "0-20" denoting the deprivation percentile of the provided block group.
		"""
		slice_ = self.adi_frame.loc[self.adi_frame.fips == fips_geocode, 'adi_quintile'].iat[0]
		return(slice_)

	def get_quintile_for_geocodes_frame(self, dataframe, geocode_column_name):
		"""
		Parameters:
		-----------
		dataframe : Pandas Dataframe
			Dataframe with a column containing geocode

		geocode_column_name : str
			Name of column in dataframe containing geocodes

		Returns
		-------
		The original dataframe with an "adi_quintile" column containing the ADI quintile.

		Notes
		-------
		Geocodes often contain leading zeroes, so be sure that the input column is correctly formatted! It should be an object or str.
		"""

		adi_ranks_only = self.adi_frame[['fips', 'adi_quintile']]
		geocodes_merged = dataframe.merge(adi_ranks_only, left_on=geocode_column_name, right_on='fips', how='left', indicator=True)

		# count up the merges
		count_merged = np.sum(geocodes_merged._merge == "both")
		count_unmerged = len(dataframe) - count_merged
		print("Geocode merge: Merged {} of {} observations in input dataframe ({}%)".format(str(count_merged), str(count_unmerged), str(round(100*count_merged/len(dataframe), 2))))

		# a little bit of error handling
		if (count_merged == 0):
			print ("Merged 0 of {} observations in input dataframe! Make sure that geocodes have been read in the correct format and watch out for the removal of leading zeroes!".format(str(len(dataframe))))

		del geocodes_merged['_merge']
		del geocodes_merged['fips']

		return(geocodes_merged['adi_quintile'].to_numpy())