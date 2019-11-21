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