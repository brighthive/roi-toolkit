import requests
import os
import pandas as pd
import json
import numpy as np

"""

# NOTE: Use batch geocoding!

Documentation

Geocoding API: https://geocoding.geo.census.gov/geocoder/Geocoding_Services_API.pdf

List of Census APIs:
https://api.census.gov/data.html

Block group API URL:
https://api.census.gov/data/2015/pdb/blockgroup	

Example call:
https://api.census.gov/data/2015/pdb/blockgroup?get=State_name,County_name,Tot_Population_CEN_2010&for=block%20group:*&in=state:01%20county:001&key=YOUR_KEY_GOES_HERE

Geocoder API information:
https://geocoding.geo.census.gov/

#### Census

# Summary of 5-year estimates
https://www.census.gov/data/developers/data-sets/acs-5year.2017.html

# Data profiles
https://www.census.gov/acs/www/data/data-tables-and-tools/data-profiles/

# Variable listing for 5-year API
https://api.census.gov/data/2017/acs/acs5/profile/variables.html

"""

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
		adi_location = "../data/adi-download/US_blockgroup_15.txt"
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

		# a little bit of error handline
		if (count_merged == 0):
			print ("Merged 0 of {} observations in input dataframe! Make sure that geocodes have been read in the correct format and watch out for the removal of leading zeroes!".format(str(len(dataframe))))

		del geocodes_merged['_merge']
		del geocodes_merged['fips']

		return(geocodes_merged)

def get_batch_geocode(addresses):
	return None

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
		print("EXCEPTION: Couldn't access vital response elements in geocodei API response:\n 	{}".format(e))
		return ""		

if __name__ == "__main__":
	adi = ADI()

	geocode_ = get_geocode_for_address("211 Hoyt Street","Brooklyn","NY")
	geocode_quintile = adi.get_quintile_for_geocode(geocode_)

