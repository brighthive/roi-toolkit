import requests
import json
import pandas as pd # using pandas here for the sake of (1) familiarity and (2) ease of extensibility
import numpy as np

"""

##### Notes #####

###### Important things to know

Important things to know from https://www.bls.gov/developers/api_faqs.htm

How many requests can I make daily?
Registered users may request up to 500 queries daily. Unregistered users may request up to 25 queries daily.
 
How many series can I include in a query?
Registered users may request up to 50 series per query. Unregistered users may request up to 25 series per query.

###### BLS API Formats

Series ID Format
https://www.bls.gov/help/hlpforma.htm
	             12345678901234567890
	Series ID    SMU19197802023800001
	Positions       Value           Field Name
	1-2             SM              Prefix
	3               U               Seasonal Adjustment Code
	4-5             19              State Code
	6-10            19780           Area Code
	11-18           20238000        SuperSector and Industry Code
	19-20           01             	Data Type Code

Data type codes

data_type_code	data_type_text
01	All Employees, In Thousands
02	Average Weekly Hours of All Employees
03	Average Hourly Earnings of All Employees, In Dollars
06	Production or Nonsupervisory Employees, In Thousands
07	Average Weekly Hours of Production Employees
08	Average Hourly Earnings of Production Employees, In Dollars
11	Average Weekly Earnings of All Employees, In Dollars
26	All Employees, 3-month average change, In Thousands, seasonally adjusted
30	Average Weekly Earnings of Production Employees, In Dollars

measure_code	measure_text
03	unemployment rate
04	unemployment
05	employment
06	labor force

"""

example_response = '{"status":"REQUEST_SUCCEEDED","responseTime":137,"message":[],"Results":{\n"series":\n[{"seriesID":"LAUST080000000000006","data":[{"year":"2019","period":"M10","periodName":"October","latest":"true","value":"3178070","footnotes":[{"code":"P","text":"Preliminary."}]},{"year":"2019","period":"M09","periodName":"September","value":"3177825","footnotes":[{}]},{"year":"2019","period":"M08","periodName":"August","value":"3173865","footnotes":[{}]},{"year":"2019","period":"M07","periodName":"July","value":"3189419","footnotes":[{}]},{"year":"2019","period":"M06","periodName":"June","value":"3186284","footnotes":[{}]},{"year":"2019","period":"M05","periodName":"May","value":"3127934","footnotes":[{}]},{"year":"2019","period":"M04","periodName":"April","value":"3119039","footnotes":[{}]},{"year":"2019","period":"M03","periodName":"March","value":"3123249","footnotes":[{}]},{"year":"2019","period":"M02","periodName":"February","value":"3132592","footnotes":[{}]},{"year":"2019","period":"M01","periodName":"January","value":"3118999","footnotes":[{}]},{"year":"2018","period":"M13","periodName":"Annual","value":"3096358","footnotes":[{}]},{"year":"2018","period":"M12","periodName":"December","value":"3136729","footnotes":[{}]},{"year":"2018","period":"M11","periodName":"November","value":"3133401","footnotes":[{}]},{"year":"2018","period":"M10","periodName":"October","value":"3135286","footnotes":[{}]},{"year":"2018","period":"M09","periodName":"September","value":"3124018","footnotes":[{}]},{"year":"2018","period":"M08","periodName":"August","value":"3114611","footnotes":[{}]},{"year":"2018","period":"M07","periodName":"July","value":"3126894","footnotes":[{}]},{"year":"2018","period":"M06","periodName":"June","value":"3115771","footnotes":[{}]},{"year":"2018","period":"M05","periodName":"May","value":"3071539","footnotes":[{}]},{"year":"2018","period":"M04","periodName":"April","value":"3060983","footnotes":[{}]},{"year":"2018","period":"M03","periodName":"March","value":"3056824","footnotes":[{}]},{"year":"2018","period":"M02","periodName":"February","value":"3054983","footnotes":[{}]},{"year":"2018","period":"M01","periodName":"January","value":"3025258","footnotes":[{}]},{"year":"2017","period":"M13","periodName":"Annual","value":"2992412","footnotes":[{}]},{"year":"2017","period":"M12","periodName":"December","value":"3022280","footnotes":[{}]},{"year":"2017","period":"M11","periodName":"November","value":"3027893","footnotes":[{}]},{"year":"2017","period":"M10","periodName":"October","value":"3030716","footnotes":[{}]},{"year":"2017","period":"M09","periodName":"September","value":"3035085","footnotes":[{}]},{"year":"2017","period":"M08","periodName":"August","value":"3019660","footnotes":[{}]},{"year":"2017","period":"M07","periodName":"July","value":"3019734","footnotes":[{}]},{"year":"2017","period":"M06","periodName":"June","value":"3007314","footnotes":[{}]},{"year":"2017","period":"M05","periodName":"May","value":"2966441","footnotes":[{}]},{"year":"2017","period":"M04","periodName":"April","value":"2957983","footnotes":[{}]},{"year":"2017","period":"M03","periodName":"March","value":"2952018","footnotes":[{}]},{"year":"2017","period":"M02","periodName":"February","value":"2945602","footnotes":[{}]},{"year":"2017","period":"M01","periodName":"January","value":"2924216","footnotes":[{}]}]}]\n}}'

BLS_API_KEY = "" # unnecessary for BLS series 1.0 api

class Parameters:
	BLS_measure_codes = {
		"unemployment rate": "03",
		"unemployment": "04",
		"employment": "05",
		"labor force": "06"
	}

class BLS_API:
	def employment_series_id(prefix="LA", seasonal_adjustment_code="U", area_code="ST0800000000000", measure_code="employment"):
		"""
		Returns absolute numbers
		"""
		measure_code = Parameters.BLS_measure_codes[measure_code]
		series_id = prefix + seasonal_adjustment_code + area_code + measure_code
		return series_id

	def wages_series_id(prefix="SM", seasonal_adjustment_code="U", state_code="05", area_code="00000", supersector_industry_code="00000000", data_type_code="01"):
		series_id = prefix + seasonal_adjustment_code + state_code + area_code + supersector_industry_code + data_type_code
		return series_id

	def get_series(seriesid, startyear, endyear):
		url = ("https://api.bls.gov/publicAPI/v1/timeseries/data/{}?startyear={}&endyear={}".format(seriesid, startyear, endyear))
		response = requests.get(url)
		content = response.content
		return content

	def parse_api_response(json_response):
		parsed = json.loads(json_response)
		data_only = parsed['Results']['series'][0]['data']
		data_frame = pd.DataFrame(data_only)

		# remove unnecessary columns
		data_frame = data_frame.drop(['footnotes', 'latest', 'period'], axis=1)

		# errors are coerced so that "Annual" dates go to NaN
		data_frame['month_year'] = pd.to_datetime(data_frame.periodName + " " + data_frame.year, format='%B %Y', errors='coerce').dt.to_period('M')

		return(data_frame)

class Calculations:
	"""
	Functions that take in dataframes produced by the BLS API and calculate statistics that will feed into ROI metrics.

	Methods
	-------
	employment_change(bls_employment_table, start_month, start_year, end_month, end_year)
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
		start_month_year = pd.to_datetime(start_month).to_period('M')
		end_month_year = pd.to_datetime(end_month).to_period('M')

		# get employment figures
		start_employment = bls_employment_table.loc[bls_employment_table.month_year == start_month, 'value'].astype(int).iat[0]
		end_employment = bls_employment_table.loc[bls_employment_table.month_year == end_month, 'value'].astype(int).iat[0]

		# get labor force figures
		start_labor_force = bls_labor_force_table.loc[bls_labor_force_table.month_year == start_month, 'value'].astype(int).iat[0]
		end_labor_force = bls_labor_force_table.loc[bls_labor_force_table.month_year == end_month, 'value'].astype(int).iat[0]

		# calculation
		employment_change = float((end_employment / end_labor_force) - (start_employment / start_labor_force))

		return employment_change

	def wage_change(bls_employment_table, start_month, start_year, end_month, end_year):
		return None



if __name__ == "__main__":

	'''
	# series ids
	employment_series_id = BLS_API.employment_series_id(measure_code="employment")
	labor_force_series_id = BLS_API.employment_series_id(measure_code="labor force")
	
	# series retreived
	employment_raw = BLS_API.get_series(employment_series_id, 2014, 2018)
	labor_force_raw = BLS_API.get_series(labor_force_series_id, 2014, 2018)

	# to dataframes
	employment = BLS_API.parse_api_response(employment_raw)
	labor_force = BLS_API.parse_api_response(labor_force_raw)

	employment.to_pickle('employment_pickled.pkl')
	labor_force.to_pickle('labor_force_pickled.pkl')
	'''

	employment = pd.read_pickle('employment_pickled.pkl')
	labor_force = pd.read_pickle('labor_force_pickled.pkl')

	employment_change_example = Calculations.employment_change(employment, labor_force, "2017-09", "2017-01")

	print(employment_change_example)


