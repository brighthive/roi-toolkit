import requests
import os

"""

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

#### Constructing National Cancer Institute SES

Without immediate access to the SEER data, we'll have to construct SES indices ourselves here. We'll calculate using SEER's methodology (https://seer.cancer.gov/seerstat/databases/census-tract/index.html)

Some of these variables are available from IPUMS (ACS), but the smallest region available from IPUMS is the PUMA, which contains several tracts.
Tracts contain several block groups.

A guide to constructing these variables (via SEER) is here: https://seer.cancer.gov/seerstat/variables/countyattribs/time-dependent.html

There are seven variables:
1) Median household income
2) Median house value
3) Median rent
4) Percent below 150% of poverty line (not in IPUMS?)
50 Education Index (Liu et al., 1998) (???)
6) Percent working class (not in IPUMS?)
7) Percent unemployed

Sources for this
Yu et al 2014 - https://www.ncbi.nlm.nih.gov/pubmed/24178398
Lieu et al 1998 - https://www.ncbi.nlm.nih.gov/pubmed/9794168

# article
https://link.springer.com/article/10.1007%2Fs11524-015-9959-y

#### Other SES measures

(Census-based socioeconomic indicators for monitoring injury causes in the USA: a review)
https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4518757/

(Validating the Use of Census Data on Education as a Measure of Socioeconomic Status in an Occupational Cohort.)
https://www.ncbi.nlm.nih.gov/pubmed/30451561

(Measuring Socioeconomic Status (SES) in the NCVS: Background, Options, and Recommendations)
https://www.bjs.gov/content/pub/pdf/Measuring_SES-Paper_authorship_corrected.pdf

#### Area Deprivation Index
https://www.neighborhoodatlas.medicine.wisc.edu/




"""

api_key = ""

def get_geocode_for_address(address, city, state_code):
	url = "https://geocoding.geo.census.gov/geocoder/geographies/address?street={}&city={}&state={}&benchmark=9&format=json&vintage=Census2010_Census2010".format(address, city, state_code)
	response = requests.get(url)
	response_content = response.content
	return response_content

def get_geocode_data(geocode):
	url = ("https://api.census.gov/data/2015/pdb/blockgroup?get=State_name,County_name,Tot_Population_CEN_2010&for=block%20group:3&in=state:36%20county:047&key=83ea085e6097fe91bbfe7bf60ca905a272850cfa")
	response = requests.get(url)
	response_content = resopnse.content
	return response_content

if __name__ == "__main__":
	a = get_geocode_for_address("102 Bergen St.","Brooklyn","NY")
	print(a)