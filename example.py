import pandas as pd
import numpy as np
from roi import metrics, types, external, equity, utilities, macro, cost
from roi.utilities import Local_Data
from datetime import date
import sys
from matplotlib import pyplot as plt
#print(sys.modules.keys())

if __name__ == "__main__":

	#bls = macro.BLS_Ops()
	#conversion = bls.get_single_year_adjustment_factor(2002,2018)
	#print(conversion)
	#exit()

	programs_data = pd.read_csv("testing/testing-data/programs.csv")

	test_microdata = pd.read_csv("testing/testing-data/test_microdata.csv")
	test_microdata['age_at_start'] = test_microdata['age'] - (date.today().year - test_microdata['program_start'])
	test_microdata['age_group_at_start'] = utilities.age_to_group(test_microdata['age_at_start'])

	# Create an age group column. The provided data has an age column denoting CURRENT age... but we want age at start

	#print(test_microdata.head())

	###### basic functions  ######

	# Get earnings summary from test microdata

	# test_summary = metrics.Summary(test_microdata, 'earnings_end')
	# stats = test_summary.earnings_summaries(['program'])
	# print(stats)

	# Calculate the individual-level earnings premium for a single individual

	#prem = metrics.Premium()
	#premium_test = prem.mincer_based_wage_change(state=36, prior_education=92, current_age=30, starting_wage=10000, years_passed=4)
	#print(premium_test)
	#exit()

	# Calculate the individual-level earnings premia for all rows in a dataframe

	#prem = metrics.Premium()
	#premium_calc = prem.Full_Earnings_Premium(test_microdata, 'earnings_start', 'earnings_end', 'program_start', 'program_end','age','08','education_level')
	#print(premium_calc)
	#exit()

	# Calculate program-level earnings premium statistics!

	# prem = metrics.Premium()
	# premium_calc = prem.Group_Earnings_Premium(test_microdata, 'earnings_start', 'earnings_end', 'program_start', 'program_end','age','state','education_level','program')
	# print(premium_calc)
	# exit()

	###### getting a bit more complicated ######

	# Calculate Theil T ratio for earnings

	# First we need to get an earnings column
	#prem = metrics.Premium()
	#premium_calc = prem.Full_Earnings_Premium(test_microdata, 'earnings_start', 'earnings_end', 'program_start', 'program_end','age','state','education_level')
	# Now we calculate inequality across races
	#theil_t_1= equity.Theil_T.Ratio_From_DataFrame(premium_calc, 'earnings_end', 'race') # final earnings is always positive - but earnings premium can be negative, so Theil can't be used!

#	# Inequality in earnings premium
	# groups, values = equity.dataframe_groups_to_ndarray(premium_calc, 'race', 'earnings_premium')
	# ratio = equity.Variance_Analysis.Ratio(groups, values)
	# print(ratio)
	# exit()

	###### geocode address ######

	#print(geo.State_To_FIPS("CA"))
	#exit()

	# Calculate program-level inequality stats for a given variable (premium here)
	#example_address = test_microdata.iloc[0]
	#geocode = geo.Census.get_geocode_for_address(example_address['Address'], example_address['City'], example_address['State'])
	#print(geocode)
	'''
	# Batch geocode addresses and fetch SES quintiles
	example_addresses = test_microdata.iloc[2:10]
	addresses_frame = example_addresses[['id','Address','City','State','Zip']]
	example_addresses['geocode'] = geo.Census.get_batch_geocode(addresses_frame)
	adi = geo.ADI()
	example_addresses['quintile'] =  adi.get_quintile_for_geocodes_frame(example_addresses, 'geocode')

	# get inequality across quintiles
	groups, values = equity.dataframe_groups_to_ndarray(example_addresses, 'quintile', 'earnings_end')
	ratio = equity.ANOVA.Ratio(groups, values)
	print(ratio)
	exit()
	'''
	# Read in data and create objects
	# programs = types.Programs(programs_data, "programs", "degree", program_length='length')
	# records = types.WageRecord(test_microdata, 'id', 'program')

	# Completion
	'''
	completion = completion.Completion(test_microdata, 'program', 'program_start', 'program_end', 'completer')
	print(completion.completion_rates)
	print(completion.time_to_completion)
	'''

	# Employment
	#test_microdata['start_month_year'] = test_microdata['program_start'].astype(str) + '-' + test_microdata['start_month'].astype(str).str.pad(2, fillchar='0')
	#test_microdata['end_month_year'] = test_microdata['program_end'].astype(str) + '-' + test_microdata['end_month'].astype(str).str.pad(2, fillchar='0')
	#employment = metrics.Employment_Likelihood(test_microdata, 'program', 'start_month_year', 'end_month_year', 'employed_at_end', 'employed_at_start','age_group_at_start','state')
	#print(employment.employment_premium)
	#exit()
	#exit()

	# Testing equity class
	#metric_test = equity.Metric.from_dataframe(test_microdata, 'program', 'earnings_end')
	#metric_test.viz.savefig('hello.png')
	#vartest = equity.Theil_L.from_dataframe(test_microdata, 'program', 'earnings_end')
	#vartest.calculate()
	#print(vartest.nans)
	#gini_test.viz.savefig('hello.png')

	# Get average wage change for a given age group and state across years, based on CPS data

	#changes = prem.wage_change_across_years(start_year=2012, end_year=2016, age_group_at_start="19-25", statefip=8)
	#print(changes)

	# For a given dataframe, create a new column for the baseline wage change across years

	#test_microdata['start_year'] = 2011
	#test_microdata['end_year'] = 2015
	#test_microdata['statefip'] = utilities.check_state_code_series(test_microdata['state'])
	#prem = metrics.Earnings_Premium(test_microdata, 'statefip', 'education_level', 'earnings_start', 'earnings_end', 'start_year', 'end_year', 'age')
	#test_microdata['predicted'] = prem.predicted_wage
	#test_microdata['raw_change'] = test_microdata['earnings_end'] - test_microdata['earnings_start']
	#test_microdata['premium'] = prem.full_premium
	#premiums_by_race = prem.group_average_premiums(['program','race'])
	#print(premiums_by_race)

	# fetch employment change 
	#bls_api = external.BLS_API(query=False)
	#employment = bls_api.bls_employment_series
	#laborforce = bls_api.bls_laborforce_series
	#change = macro.Calculations.employment_change(employment, laborforce, "08", "2012-07","2018-10")
	#print(change)

	#bls_api = external.BLS_API()
	#cpi_range = bls_api.get_cpi_adjustment_range(2002, 2005) # get annual CPI-U index for all years in intervening range
	#cpi_range_oneyear = bls_api.get_cpi_adjustment(1999, 2020) # get CPI-U adjustment factor between the two years provided
	#print(cpi_range_oneyear)
	#exit()

	# adjust starting wages
	#ops = macro.BLS_Ops()
	#test_microdata['adjusted_start_wage'] = ops.adjust_to_current_dollars(test_microdata, 'start_year', 'earnings_start')
	#print(test_microdata)

	# employment change in one state over time
	#test_microdata['end_month'] = pd.to_datetime(dict(year='2012', month=test_microdata['start_month'], day=1)).dt.strftime('%Y-%m')
	#test_microdata['start_month'] = pd.to_datetime(dict(year='2011', month=test_microdata['start_month'], day=1)).dt.strftime('%Y-%m')
	#test_microdata['statefip'] = utilities.State_To_FIPS_series(test_microdata['State'])

	#bls = macro.BLS_Ops()
	#test_microdata['employment_change'] = bls.employment_change(test_microdata['statefip'], test_microdata['start_month'], test_microdata['end_month'])
	#test_microdata['wage_change'] = bls.wage_change(test_microdata['statefip'], test_microdata['start_month'], test_microdata['end_month'], convert=True)

	# CPI adjustment
	#bls = macro.BLS_Ops()
	#test_microdata['fixed_dollars'] = bls.adjust_to_current_dollars(test_microdata, 'program_start', 'earnings_start')
	#print(test_microdata)

	# Testing equity class
	#gini_test = equity.Gini.from_dataframe(test_microdata, 'program', 'earnings_end', sample=100)
	#gini_test.calculate()
	#print(gini_test.ratio)
	#print(gini_test.sample)

	sample_loan = cost.Compound_Interest_Loan.calculate_period_payment(10000, 0.05, 24)
	balance_remaining = cost.Compound_Interest_Loan.amount_to_be_paid_after_n_periods(10000,0.05,24,23)
	print(sample_loan)
	print(balance_remaining)



