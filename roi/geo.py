import requests
import os
import pandas as pd
import json
import numpy as np
from io import StringIO
from roi import settings
from roi.utilities import State_To_FIPS

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